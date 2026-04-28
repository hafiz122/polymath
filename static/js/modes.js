/**
 * 2-Player Local Arithmetic Game Engine
 * Pure client-side, no server communication.
 */

(function () {
    // ---- State ----
    let currentMode = null;
    let totalRounds = 10;
    let currentRound = 0;
    let roundActive = false;
    let players = {
        1: { name: 'Player 1', score: 0, streak: 0, keyMap: { 0: 'q', 1: 'w', 2: 'e', 3: 'r' } },
        2: { name: 'Player 2', score: 0, streak: 0, keyMap: { 0: 'u', 1: 'i', 2: 'o', 3: 'p' } },
    };
    let currentProblem = null;
    let timerRaf = null;
    let roundTime = 15;
    let totalTimeMs = 0;

    // ---- DOM Refs ----
    const screens = {
        select: document.getElementById('mode-select'),
        setup: document.getElementById('mode-setup'),
        game: document.getElementById('mode-game'),
        results: document.getElementById('mode-results'),
    };

    const els = {
        p1NameInput: document.getElementById('p1-name'),
        p2NameInput: document.getElementById('p2-name'),
        roundsInput: document.getElementById('rounds-select'),
        startBtn: document.getElementById('start-local-btn'),
        backBtn: document.getElementById('back-to-modes-btn'),
        p1DisplayName: document.getElementById('p1-display-name'),
        p2DisplayName: document.getElementById('p2-display-name'),
        p1Score: document.getElementById('p1-score'),
        p2Score: document.getElementById('p2-score'),
        p1Streak: document.getElementById('p1-streak'),
        p2Streak: document.getElementById('p2-streak'),
        p1Panel: document.getElementById('p1-panel'),
        p2Panel: document.getElementById('p2-panel'),
        roundNum: document.getElementById('local-round-num'),
        roundTotal: document.getElementById('local-round-total'),
        timerBar: document.getElementById('local-timer-bar'),
        problem: document.getElementById('local-problem'),
        options: document.getElementById('local-options'),
        feedback: document.getElementById('local-feedback'),
        p1Result: document.getElementById('p1-result'),
        p2Result: document.getElementById('p2-result'),
        winner: document.getElementById('local-winner'),
        playAgainBtn: document.getElementById('play-again-local-btn'),
        // Tabletop mobile refs
        desktopView: document.getElementById('desktop-game-view'),
        tabletopView: document.getElementById('tabletop-game-view'),
        ttP1Name: document.getElementById('tt-p1-name'),
        ttP2Name: document.getElementById('tt-p2-name'),
        ttP1Score: document.getElementById('tt-p1-score'),
        ttP2Score: document.getElementById('tt-p2-score'),
        ttP1Streak: document.getElementById('tt-p1-streak'),
        ttP2Streak: document.getElementById('tt-p2-streak'),
        ttProblemTop: document.getElementById('tt-problem-top'),
        ttProblemBottom: document.getElementById('tt-problem-bottom'),
        ttOptionsTop: document.getElementById('tt-options-top'),
        ttOptionsBottom: document.getElementById('tt-options-bottom'),
        ttTimerTop: document.getElementById('tt-timer-top'),
        ttTimerBottom: document.getElementById('tt-timer-bottom'),
        ttFeedbackTop: document.getElementById('tt-feedback-top'),
        ttFeedbackBottom: document.getElementById('tt-feedback-bottom'),
    };

    // ---- Mobile detection ----
    function isMobile() {
        return window.innerWidth <= 768;
    }

    function setGameLayout() {
        if (isMobile()) {
            els.desktopView.classList.add('hidden');
            els.tabletopView.classList.remove('hidden');
        } else {
            els.desktopView.classList.remove('hidden');
            els.tabletopView.classList.add('hidden');
        }
    }

    // ---- Utilities ----
    function showScreen(name) {
        Object.values(screens).forEach(s => s.classList.add('hidden'));
        screens[name].classList.remove('hidden');
    }

    function randInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    function shuffle(arr) {
        const a = arr.slice();
        for (let i = a.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [a[i], a[j]] = [a[j], a[i]];
        }
        return a;
    }

    function clearChildren(el) {
        while (el.firstChild) el.removeChild(el.firstChild);
    }

    // ---- Problem Generators ----
    function genAddition() {
        const a = randInt(10, 99);
        const b = randInt(10, 99);
        const ans = a + b;
        return {
            text: `${a} + ${b} = ?`,
            answer: ans,
            options: makeOptions(ans, 20, 60),
        };
    }

    function genSubtraction() {
        const a = randInt(10, 99);
        const b = randInt(1, a - 1);
        const ans = a - b;
        return {
            text: `${a} - ${b} = ?`,
            answer: ans,
            options: makeOptions(ans, 10, 30),
        };
    }

    function genMultiplication() {
        const a = randInt(2, 12);
        const b = randInt(2, 12);
        const ans = a * b;
        return {
            text: `${a} × ${b} = ?`,
            answer: ans,
            options: makeOptions(ans, 5, 30),
        };
    }

    function genDivision() {
        const b = randInt(2, 12);
        const ans = randInt(2, 12);
        const a = b * ans;
        return {
            text: `${a} ÷ ${b} = ?`,
            answer: ans,
            options: makeOptions(ans, 1, 8),
        };
    }

    function makeOptions(correct, spreadMin, spreadMax) {
        const opts = new Set([correct]);
        let attempts = 0;
        while (opts.size < 4 && attempts < 100) {
            const d = correct + randInt(-spreadMax, spreadMax);
            if (d !== correct && d >= 0) opts.add(d);
            attempts++;
        }
        return shuffle(Array.from(opts));
    }

    const generators = {
        addition: genAddition,
        subtraction: genSubtraction,
        multiplication: genMultiplication,
        division: genDivision,
    };

    // ---- Screens ----
    function initSelect() {
        document.querySelectorAll('.mode-card').forEach(card => {
            card.addEventListener('click', () => {
                currentMode = card.dataset.mode;
                showScreen('setup');
            });
        });
    }

    function initSetup() {
        els.startBtn.addEventListener('click', () => {
            players[1].name = els.p1NameInput.value.trim() || 'Player 1';
            players[2].name = els.p2NameInput.value.trim() || 'Player 2';
            totalRounds = parseInt(els.roundsInput.value, 10) || 10;
            startGame();
        });
        els.backBtn.addEventListener('click', () => {
            currentMode = null;
            showScreen('select');
        });
    }

    function startGame() {
        players[1].score = 0;
        players[1].streak = 0;
        players[2].score = 0;
        players[2].streak = 0;
        currentRound = 0;

        els.p1DisplayName.textContent = players[1].name;
        els.p2DisplayName.textContent = players[2].name;
        els.ttP1Name.textContent = players[1].name;
        els.ttP2Name.textContent = players[2].name;
        setGameLayout();
        updateScores();
        showScreen('game');
        startRound();
    }

    function startRound() {
        currentRound++;
        roundActive = true;
        els.roundNum.textContent = currentRound;
        els.roundTotal.textContent = '/ ' + totalRounds;
        els.feedback.textContent = '';
        els.feedback.className = 'local-feedback';
        els.ttFeedbackTop.textContent = '';
        els.ttFeedbackTop.className = 'tabletop-feedback';
        els.ttFeedbackBottom.textContent = '';
        els.ttFeedbackBottom.className = 'tabletop-feedback';

        const gen = generators[currentMode];
        currentProblem = gen();

        els.problem.textContent = currentProblem.text;
        els.ttProblemTop.textContent = currentProblem.text;
        els.ttProblemBottom.textContent = currentProblem.text;
        renderOptions(currentProblem.options);

        totalTimeMs = roundTime * 1000;
        startTimer();
    }

    function createOptionButton(opt, idx, playerNum) {
        const btn = document.createElement('div');
        btn.className = 'local-option';
        btn.dataset.idx = idx;

        const val = document.createElement('span');
        val.className = 'local-option-val';
        val.textContent = opt;
        btn.appendChild(val);

        if (!isMobile()) {
            const keys = document.createElement('span');
            keys.className = 'local-option-keys';
            const k1 = players[1].keyMap[idx].toUpperCase();
            const k2 = players[2].keyMap[idx].toUpperCase();
            keys.textContent = `${k1} / ${k2}`;
            btn.appendChild(keys);
        }

        if (playerNum === 1 || playerNum === 2) {
            btn.addEventListener('click', () => {
                handleAnswer(playerNum, idx);
            });
        }

        return btn;
    }

    function renderOptions(options) {
        clearChildren(els.options);
        clearChildren(els.ttOptionsTop);
        clearChildren(els.ttOptionsBottom);

        options.forEach((opt, idx) => {
            // Desktop
            const desktopBtn = createOptionButton(opt, idx, 0); // 0 = any player on desktop
            els.options.appendChild(desktopBtn);

            // Mobile tabletop - P1 buttons
            const topBtn = createOptionButton(opt, idx, 1);
            els.ttOptionsTop.appendChild(topBtn);

            // Mobile tabletop - P2 buttons
            const bottomBtn = createOptionButton(opt, idx, 2);
            els.ttOptionsBottom.appendChild(bottomBtn);
        });
    }

    function startTimer() {
        stopTimer();
        const startTime = performance.now();
        const duration = totalTimeMs;

        function tick(now) {
            if (!roundActive) return;
            const elapsed = now - startTime;
            const remaining = Math.max(0, duration - elapsed);
            const pct = (remaining / duration) * 100;
            els.timerBar.style.width = pct + '%';
            els.ttTimerTop.style.width = pct + '%';
            els.ttTimerBottom.style.width = pct + '%';

            if (remaining <= 0) {
                stopTimer();
                endRound(null, false);
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

    function handleAnswer(playerNum, optionIdx) {
        if (!roundActive) return;
        const answer = currentProblem.options[optionIdx];
        const isCorrect = answer === currentProblem.answer;

        roundActive = false;
        stopTimer();

        // Highlight buttons (desktop + tabletop)
        const allContainers = [els.options, els.ttOptionsTop, els.ttOptionsBottom];
        allContainers.forEach(container => {
            const btns = container.querySelectorAll('.local-option');
            btns.forEach((btn, i) => {
                const val = currentProblem.options[i];
                if (val === currentProblem.answer) {
                    btn.classList.add('correct');
                }
                if (i === optionIdx && !isCorrect) {
                    btn.classList.add('wrong');
                }
            });
        });

        // Score
        if (isCorrect) {
            const p = players[playerNum];
            p.streak += 1;
            const streakBonus = Math.min(p.streak * 10, 50);
            p.score += 100 + streakBonus;
            els.feedback.textContent = `${p.name} correct! +${100 + streakBonus}`;
            els.feedback.className = 'local-feedback correct-feedback';
            els.ttFeedbackTop.textContent = `${p.name} correct! +${100 + streakBonus}`;
            els.ttFeedbackTop.className = 'tabletop-feedback correct-feedback';
            els.ttFeedbackBottom.textContent = `${p.name} correct! +${100 + streakBonus}`;
            els.ttFeedbackBottom.className = 'tabletop-feedback correct-feedback';
        } else {
            const wrongPlayer = players[playerNum];
            const otherPlayerNum = playerNum === 1 ? 2 : 1;
            const stealingPlayer = players[otherPlayerNum];
            const stolenAmount = Math.floor(wrongPlayer.score * 0.8);
            wrongPlayer.score -= stolenAmount;
            stealingPlayer.score += stolenAmount;
            wrongPlayer.streak = 0;
            const msg = `${wrongPlayer.name} wrong! ${stealingPlayer.name} steals ${stolenAmount} pts!`;
            els.feedback.textContent = msg;
            els.feedback.className = 'local-feedback wrong-feedback';
            els.ttFeedbackTop.textContent = msg;
            els.ttFeedbackTop.className = 'tabletop-feedback wrong-feedback';
            els.ttFeedbackBottom.textContent = msg;
            els.ttFeedbackBottom.className = 'tabletop-feedback wrong-feedback';
        }

        updateScores();

        setTimeout(() => {
            if (currentRound >= totalRounds) {
                showResults();
            } else {
                startRound();
            }
        }, 1500);
    }

    function endRound(playerNum, isCorrect) {
        if (!roundActive) return;
        roundActive = false;
        stopTimer();

        // Show correct answer (desktop + tabletop)
        const allContainers = [els.options, els.ttOptionsTop, els.ttOptionsBottom];
        allContainers.forEach(container => {
            const btns = container.querySelectorAll('.local-option');
            btns.forEach((btn, i) => {
                if (currentProblem.options[i] === currentProblem.answer) {
                    btn.classList.add('correct');
                }
            });
        });

        els.feedback.textContent = `Time up! Answer: ${currentProblem.answer}`;
        els.feedback.className = 'local-feedback wrong-feedback';
        els.ttFeedbackTop.textContent = `Time up! Answer: ${currentProblem.answer}`;
        els.ttFeedbackTop.className = 'tabletop-feedback wrong-feedback';
        els.ttFeedbackBottom.textContent = `Time up! Answer: ${currentProblem.answer}`;
        els.ttFeedbackBottom.className = 'tabletop-feedback wrong-feedback';

        setTimeout(() => {
            if (currentRound >= totalRounds) {
                showResults();
            } else {
                startRound();
            }
        }, 1500);
    }

    function updateScores() {
        els.p1Score.textContent = players[1].score;
        els.p2Score.textContent = players[2].score;
        els.p1Streak.textContent = players[1].streak > 1 ? '🔥 ' + players[1].streak : '';
        els.p2Streak.textContent = players[2].streak > 1 ? '🔥 ' + players[2].streak : '';
        // Tabletop
        els.ttP1Score.textContent = players[1].score;
        els.ttP2Score.textContent = players[2].score;
        els.ttP1Streak.textContent = players[1].streak > 1 ? '🔥 ' + players[1].streak : '';
        els.ttP2Streak.textContent = players[2].streak > 1 ? '🔥 ' + players[2].streak : '';
    }

    function showResults() {
        showScreen('results');

        const p1Name = players[1].name;
        const p2Name = players[2].name;
        const p1Score = players[1].score;
        const p2Score = players[2].score;

        els.p1Result.querySelector('.local-result-name').textContent = p1Name;
        els.p1Result.querySelector('.local-result-score').textContent = p1Score;
        els.p2Result.querySelector('.local-result-name').textContent = p2Name;
        els.p2Result.querySelector('.local-result-score').textContent = p2Score;

        let winnerText = '';
        if (p1Score > p2Score) {
            winnerText = `${p1Name} wins!`;
            els.p1Result.classList.add('winner');
            els.p2Result.classList.remove('winner');
        } else if (p2Score > p1Score) {
            winnerText = `${p2Name} wins!`;
            els.p1Result.classList.remove('winner');
            els.p2Result.classList.add('winner');
        } else {
            winnerText = "It's a tie!";
            els.p1Result.classList.add('winner');
            els.p2Result.classList.add('winner');
        }
        els.winner.textContent = winnerText;
    }

    // ---- Keyboard ----
    document.addEventListener('keydown', (e) => {
        if (!roundActive) return;
        const key = e.key.toLowerCase();

        // P1 keys: q/w/e/r
        const p1Idx = Object.values(players[1].keyMap).indexOf(key);
        if (p1Idx !== -1) {
            e.preventDefault();
            handleAnswer(1, p1Idx);
            return;
        }

        // P2 keys: u/i/o/p
        const p2Idx = Object.values(players[2].keyMap).indexOf(key);
        if (p2Idx !== -1) {
            e.preventDefault();
            handleAnswer(2, p2Idx);
            return;
        }
    });

    // ---- Resize handler ----
    window.addEventListener('resize', () => {
        if (!screens.game.classList.contains('hidden')) {
            setGameLayout();
        }
    });

    // ---- Init ----
    initSelect();
    initSetup();

    if (els.playAgainBtn) {
        els.playAgainBtn.addEventListener('click', () => {
            startGame();
        });
    }
})();
