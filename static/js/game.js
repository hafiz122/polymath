/**
 * Polygon Speed Math Game Client
 * Handles WebSocket communication, UI state, timer, and answer submission.
 */

(function () {
    // ---- Config ----
    const ROOM_ID = document.querySelector('meta[name="room-id"]')?.content;
    const WS_URL = `ws://${window.location.host}/ws/rooms/${ROOM_ID}`;

    // ---- State ----
    let ws = null;
    let myPlayerId = null;
    let isHost = false;
    let timerInterval = null;
    let timerRaf = null;
    let timeLeft = 0;
    let totalTime = 0;
    let roundActive = false;
    let currentCorrectAnswer = null;
    let useTimer = true;

    // ---- DOM Refs ----
    const screens = {
        lobby: document.getElementById('lobby-screen'),
        game: document.getElementById('game-screen'),
        results: document.getElementById('results-screen'),
    };

    const els = {
        displayRoomCode: document.getElementById('display-room-code'),
        roomStatus: document.querySelector('.room-status'),
        playerList: document.getElementById('player-list'),
        settingRounds: document.getElementById('setting-rounds'),
        settingTime: document.getElementById('setting-time'),
        settingDifficulty: document.getElementById('setting-difficulty'),
        settingTimer: document.getElementById('setting-timer'),
        timerContainer: document.getElementById('timer-container'),
        startGameBtn: document.getElementById('start-game-btn'),
        hostHint: document.getElementById('host-hint'),
        roundNumber: document.getElementById('round-number'),
        roundTotal: document.getElementById('round-total'),
        timerBar: document.getElementById('timer-bar'),
        timerText: document.getElementById('timer-text'),
        problemText: document.getElementById('problem-text'),
        problemDiagram: document.getElementById('problem-diagram'),
        optionsGrid: document.getElementById('options-grid'),
        answerFeedback: document.getElementById('answer-feedback'),
        liveScoreboard: document.getElementById('live-scoreboard'),
        podium: document.getElementById('podium'),
        finalScoreboard: document.getElementById('final-scoreboard'),
        playAgainBtn: document.getElementById('play-again-btn'),
    };

    // ---- Utilities ----
    function showScreen(name) {
        Object.values(screens).forEach(s => s.classList.add('hidden'));
        screens[name].classList.remove('hidden');
    }

    function clearChildren(el) {
        while (el.firstChild) el.removeChild(el.firstChild);
    }

    function renderMathBlocks(text) {
        if (typeof katex === 'undefined') {
            console.warn('KaTeX not loaded - using plain text fallback');
            return text.replace(/\$([^$]+)\$/g, '$1');
        }
        // Replace inline math $...$ with KaTeX rendered HTML
        return text.replace(/\$([^$]+)\$/g, (match, latex) => {
            try {
                return katex.renderToString(latex.trim(), {throwOnError: false, displayMode: false});
            } catch (e) {
                console.error('KaTeX render error:', e);
                return match;
            }
        });
    }

    function diffLabel(n) {
        if (n <= 1) return 'Easy';
        if (n === 2) return 'Medium';
        return 'Hard';
    }

    // ---- WebSocket ----
    function connect() {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            console.log('WebSocket connected');
            // Keep-alive ping
            setInterval(() => {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ action: 'ping' }));
                }
            }, 30000);
        };

        ws.onmessage = (event) => {
            let msg;
            try {
                msg = JSON.parse(event.data);
            } catch (e) {
                console.error('Invalid JSON', event.data);
                return;
            }
            handleMessage(msg);
        };

        ws.onclose = () => {
            console.log('WebSocket closed, reconnecting in 2s...');
            setTimeout(connect, 2000);
        };

        ws.onerror = (err) => {
            console.error('WebSocket error', err);
        };
    }

    function send(action, payload = {}) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action, ...payload }));
        }
    }

    // ---- Message Handlers ----
    function handleMessage(msg) {
        switch (msg.type) {
            case 'room_state':
                myPlayerId = msg.you;
                updateLobby(msg.room);
                break;
            case 'player_joined':
            case 'player_left':
                updateLobby(msg.room);
                break;
            case 'game_started':
                showScreen('game');
                updateLobby(msg.room);
                break;
            case 'round_started':
                handleRoundStarted(msg);
                break;
            case 'round_ended':
                handleRoundEnded(msg);
                break;
            case 'answer_result':
                handleAnswerResult(msg);
                break;
            case 'game_finished':
                handleGameFinished(msg);
                break;
            case 'pong':
                break;
            case 'error':
                alert(msg.message || 'An error occurred');
                break;
            default:
                console.log('Unknown message type:', msg.type);
        }
    }

    // ---- Lobby ----
    function updateLobby(room) {
        if (!room) return;

        // Update settings
        els.settingRounds.textContent = room.settings.rounds;
        els.settingTime.textContent = room.settings.time_per_question + 's';
        els.settingDifficulty.textContent = diffLabel(room.settings.difficulty);
        els.settingTimer.textContent = room.settings.use_timer ? 'On' : 'Off';

        // Update players
        clearChildren(els.playerList);
        room.players.forEach(p => {
            const li = document.createElement('li');
            li.className = 'player-item';
            const nameSpan = document.createElement('span');
            nameSpan.className = 'player-name';
            nameSpan.textContent = p.name + (p.id === myPlayerId ? ' (You)' : '');
            li.appendChild(nameSpan);

            if (p.id === room.host_id) {
                const badge = document.createElement('span');
                badge.className = 'player-badge';
                badge.textContent = 'Host';
                li.appendChild(badge);
            }
            els.playerList.appendChild(li);
        });

        // Host controls
        isHost = room.host_id === myPlayerId;
        if (isHost && room.status === 'waiting') {
            els.startGameBtn.style.display = 'inline-flex';
            els.hostHint.style.display = 'none';
        } else {
            els.startGameBtn.style.display = 'none';
            els.hostHint.style.display = 'block';
        }

        // If already playing and we refreshed
        if (room.status === 'playing' && screens.game.classList.contains('hidden')) {
            showScreen('game');
        }
        if (room.status === 'finished' && screens.results.classList.contains('hidden')) {
            // We missed the finish, just show leaderboard from room state
            showScreen('results');
        }
    }

    // ---- Game ----
    function handleRoundStarted(msg) {
        roundActive = true;
        currentCorrectAnswer = null;

        els.roundNumber.textContent = msg.round;
        els.roundTotal.textContent = '/ ' + msg.total_rounds;

        // Problem text (plain text, styled with LaTeX-like font via CSS)
        els.problemText.textContent = msg.problem.question;

        // Diagram
        clearChildren(els.problemDiagram);
        if (msg.problem.svg_markup) {
            const wrapper = document.createElement('div');
            wrapper.innerHTML = msg.problem.svg_markup;
            const svg = wrapper.querySelector('svg');
            if (svg) {
                els.problemDiagram.appendChild(svg);
            }
        }

        // Options
        clearChildren(els.optionsGrid);
        msg.problem.options.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.textContent = opt;
            btn.addEventListener('click', () => submitAnswer(opt, btn));
            els.optionsGrid.appendChild(btn);
        });

        // Feedback
        els.answerFeedback.className = 'answer-feedback';
        els.answerFeedback.classList.remove('show');
        els.answerFeedback.textContent = '';

        // No math in problem text to render here; explanation math is rendered when round ends

        // Timer
        useTimer = msg.use_timer !== false;
        if (els.timerContainer) {
            els.timerContainer.style.display = useTimer ? 'flex' : 'none';
        }
        if (useTimer) {
            totalTime = msg.time_limit;
            timeLeft = msg.time_limit;
            startTimer();
        }
    }

    function startTimer() {
        stopTimer();
        if (!useTimer) return;
        const startTime = performance.now();
        const durationMs = totalTime * 1000;

        function tick(now) {
            if (!roundActive) return;
            const elapsed = now - startTime;
            const remaining = Math.max(0, durationMs - elapsed);
            timeLeft = remaining / 1000;

            const pct = (remaining / durationMs) * 100;
            els.timerBar.style.width = pct + '%';
            els.timerText.textContent = Math.ceil(timeLeft).toString();

            if (remaining <= 0) {
                stopTimer();
                disableOptions();
                return;
            }
            timerRaf = requestAnimationFrame(tick);
        }
        timerRaf = requestAnimationFrame(tick);
    }

    function stopTimer() {
        if (timerRaf) {
            cancelAnimationFrame(timerRaf);
            timerRaf = null;
        }
    }

    function disableOptions() {
        const btns = els.optionsGrid.querySelectorAll('.option-btn');
        btns.forEach(b => b.disabled = true);
    }

    function submitAnswer(answer, btnElement) {
        if (!roundActive) return;
        send('submit_answer', { answer });
        disableOptions();
        // Visual feedback on selected button will come via answer_result
        btnElement.style.borderColor = 'var(--accent)';
    }

    function handleAnswerResult(msg) {
        // Highlight correct/wrong options
        const btns = els.optionsGrid.querySelectorAll('.option-btn');
        btns.forEach(btn => {
            if (btn.textContent.trim() === currentCorrectAnswer && currentCorrectAnswer) {
                btn.classList.add('correct');
            }
            if (msg.player_id === myPlayerId) {
                if (!msg.correct && btn.textContent.trim() !== currentCorrectAnswer) {
                    // We don't highlight wrong selection globally, only for current player
                }
            }
        });

        if (msg.player_id === myPlayerId) {
            els.answerFeedback.classList.add('show');
            if (msg.correct) {
                els.answerFeedback.className = 'answer-feedback show correct-feedback';
                els.answerFeedback.innerHTML = `<strong>Correct!</strong> +${msg.points} points (${(msg.time_ms / 1000).toFixed(1)}s)`;
            } else {
                els.answerFeedback.className = 'answer-feedback show wrong-feedback';
                const correct = msg.correct_answer || currentCorrectAnswer || '?';
                els.answerFeedback.innerHTML = `<strong>Wrong!</strong> The correct answer was <strong>${correct}</strong>.`;
            }
        }

        // Refresh leaderboard with latest data from server if available
        // (actual update comes via round_ended or we can optimistically update)
    }

    function handleRoundEnded(msg) {
        roundActive = false;
        stopTimer();
        currentCorrectAnswer = msg.correct_answer;

        // Show correct answer on all option buttons
        const btns = els.optionsGrid.querySelectorAll('.option-btn');
        btns.forEach(btn => {
            btn.disabled = true;
            if (btn.textContent.trim() === msg.correct_answer) {
                btn.classList.add('correct');
            }
        });

        // Show explanation with rendered LaTeX math
        els.answerFeedback.classList.add('show');
        els.answerFeedback.className = 'answer-feedback show correct-feedback';
        const renderedExplanation = renderMathBlocks(msg.explanation);
        els.answerFeedback.innerHTML = `<strong>Answer: ${msg.correct_answer}</strong><br>${renderedExplanation}`;

        // Update live scoreboard
        updateLiveScoreboard(msg.leaderboard);
    }

    function updateLiveScoreboard(players) {
        clearChildren(els.liveScoreboard);
        if (!players || !players.length) return;

        players.forEach((p, idx) => {
            const li = document.createElement('li');
            li.className = 'scoreboard-item';
            if (p.id === myPlayerId) li.classList.add('current-player');

            const rank = document.createElement('span');
            rank.className = 'scoreboard-rank';
            rank.textContent = (idx + 1) + '.';

            const name = document.createElement('span');
            name.className = 'scoreboard-name';
            name.textContent = p.name;

            const score = document.createElement('span');
            score.className = 'scoreboard-score';
            score.textContent = p.score;

            li.appendChild(rank);
            li.appendChild(name);
            li.appendChild(score);

            if (p.streak > 1) {
                const streak = document.createElement('span');
                streak.className = 'scoreboard-streak';
                streak.textContent = '🔥 ' + p.streak;
                li.appendChild(streak);
            }

            els.liveScoreboard.appendChild(li);
        });
    }

    // ---- Results ----
    function handleGameFinished(msg) {
        showScreen('results');
        stopTimer();

        const players = msg.leaderboard || [];
        renderPodium(players);
        renderFinalScoreboard(players);
    }

    function renderPodium(players) {
        clearChildren(els.podium);
        if (!players.length) return;

        const places = [
            { idx: 0, cls: 'first', label: '1st' },
            { idx: 1, cls: 'second', label: '2nd' },
            { idx: 2, cls: 'third', label: '3rd' },
        ];

        places.forEach(place => {
            if (place.idx >= players.length) return;
            const p = players[place.idx];
            const div = document.createElement('div');
            div.className = `podium-place ${place.cls}`;

            const rank = document.createElement('div');
            rank.className = 'podium-rank';
            rank.textContent = place.label;

            const name = document.createElement('div');
            name.className = 'podium-name';
            name.textContent = p.name;

            const score = document.createElement('div');
            score.className = 'podium-score';
            score.textContent = p.score + ' pts';

            div.appendChild(rank);
            div.appendChild(name);
            div.appendChild(score);
            els.podium.appendChild(div);
        });
    }

    function renderFinalScoreboard(players) {
        clearChildren(els.finalScoreboard);
        players.forEach((p, idx) => {
            const li = document.createElement('li');
            li.className = 'scoreboard-item';
            if (p.id === myPlayerId) li.classList.add('current-player');

            const rank = document.createElement('span');
            rank.className = 'scoreboard-rank';
            rank.textContent = (idx + 1) + '.';

            const name = document.createElement('span');
            name.className = 'scoreboard-name';
            name.textContent = p.name;

            const score = document.createElement('span');
            score.className = 'scoreboard-score';
            score.textContent = p.score;

            li.appendChild(rank);
            li.appendChild(name);
            li.appendChild(score);
            els.finalScoreboard.appendChild(li);
        });
    }

    // ---- Event Listeners ----
    if (els.startGameBtn) {
        els.startGameBtn.addEventListener('click', () => {
            send('start_game');
        });
    }

    if (els.playAgainBtn) {
        els.playAgainBtn.addEventListener('click', () => {
            window.location.href = '/';
        });
    }

    // ---- Init ----
    if (ROOM_ID) {
        connect();
    }
})();
