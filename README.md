# PolyMath

A no-nonsense, real-time speed math game where you race your friends to solve polygon geometry problems. Fastest brain wins.

Built because math class was too slow and multiplayer games had too many ads.

---

## What is this?

You and your friends join a room. Someone hits **Start**. A polygon pops up with a missing angle, or a question about interior angles, or some other geometry trick. Everyone races to pick the right answer. First one gets the most points. Get it wrong and your streak resets to zero. Cry.

There's also a **2-player mode on one phone** — flip it tabletop-style, sit across from each other, and tap your half of the screen. Great for road trips, cafés, or proving you're smarter than your sibling.

---

## Features

- **Real-time multiplayer** — Create a room, share the code, play live
- **WebSocket rooms** — No polling, no lag, just instant updates
- **Polygon problems** — Triangles, quadrilaterals, regular polygons, angle sums, missing angles
- **SVG diagrams** — Clean polygon drawings generated on the fly, no images to load
- **LaTeX math** — KaTeX renders all math beautifully (no blurry screenshots)
- **Speed scoring** — 100 points base, up to +200 for speed, +50 for streaks
- **Live leaderboard** — Watch your friends' scores update in real time
- **Tabletop mode** — Play 2-player arithmetic on one phone, split-screen rotated 180°
- **Timer toggle** — Host can disable the timer for chill practice rounds
- **Brutalist design** — Thick borders, pure white, burnt orange accent. No gradients. No soft shadows. Zero border-radius.

---

## Play it now

### Online (Railway)
👉 **[polymath.up.railway.app](https://polymath.up.railway.app)** *(or your deployed URL)*

### Local

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Open http://localhost:8000
```

---

## How to play

### Multiplayer (online)

1. Enter your name → **Create Room**
2. Copy the room code and share it
3. Your friends join with the code
4. Host clicks **Start Game**
5. Solve as fast as possible. Don't choke.

### 2-Player (same phone)

1. Go to **Modes**
2. Pick Addition, Subtraction, Multiplication, or Division
3. Set player names and round count
4. Put the phone flat on the table between you
5. Each player taps their half of the screen

**Controls (desktop keyboard):**
- Player 1: `Q` `W` `E` `R`
- Player 2: `U` `I` `O` `P`

---

## Scoring

| Action | Points |
|--------|--------|
| Correct answer | 100 base |
| Speed bonus | Up to +200 (faster = more) |
| Streak bonus | +10 per consecutive correct, max +50 |
| Wrong answer | 0. Streak resets. Shame. |

---

## Problem types

- **Missing angle** — Triangle or quadrilateral with one angle hidden
- **Regular interior angle** — What's each angle in a regular polygon?
- **Exterior angle** — Same deal, but outside
- **Angle sum** — Find the total interior angles (or work backwards from the sum)
- **Polygon name** — "I have 1080° total. What am I?"
- **Sides from angle** — "Each interior angle is 140°. How many sides?"

---

## Tech stack

| Thing | What we used | Why |
|-------|-------------|-----|
| Backend | FastAPI + native WebSockets | Fast, async, no extra dependencies |
| Frontend | Jinja2 + vanilla JS | No build step, no framework bloat |
| Math rendering | KaTeX | Real LaTeX fonts, instant render |
| Diagrams | SVG (Python-generated) | Sharp at any size, no image assets |
| Styling | Custom CSS | Brutalist aesthetic, full control |

---

## Project structure

```
interactive-math/
├── main.py              # FastAPI app, routes, WebSocket handler
├── requirements.txt     # Python deps
├── render.yaml          # Railway deployment config
├── game/
│   ├── manager.py       # Room state, game loop, scoring
│   ├── generator.py     # Problem generator with 6 question types
│   └── renderer.py      # SVG polygon diagram builder
├── static/
│   ├── css/style.css    # Brutalist design system
│   ├── js/game.js       # WebSocket client (multiplayer)
│   └── js/modes.js      # 2-player local game engine
└── templates/
    ├── base.html        # Layout with KaTeX
    ├── index.html       # Landing + room forms
    ├── room.html        # Lobby → game → results
    ├── modes.html       # 2-player tabletop mode
    └── pricing.html     # (we have tiers, why not)
```

---

## Deploy your own

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/...)

Or manually:

1. Fork this repo
2. Create a Railway project → Deploy from GitHub repo
3. Railway auto-detects Python, sets the build command
4. Add environment variable: `PORT = 8000`
5. Deploy

Free tier ($5 credit) is enough for light usage.

---

## License

MIT — do whatever you want. Just don't sell it back to your math teacher.

---

*Built with caffeine, stubbornness, and a refusal to use React.*
