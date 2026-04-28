# PolyMath — Polygon Speed Math Game

A competitive, real-time speed math game where players race to solve polygon geometry problems. Built with FastAPI and WebSockets.

## Features

- **Real-time multiplayer** — Create or join rooms, compete live against friends
- **Polygon topics** — Missing angles, interior/exterior angles, angle sums, polygon identification
- **Beautiful SVG diagrams** — Clean, animated polygon drawings with labeled angles
- **LaTeX math rendering** — All math text rendered in true LaTeX font via KaTeX
- **Speed scoring** — Faster correct answers earn more points + streak bonuses
- **Live leaderboard** — Watch scores update in real-time as you play
- **Responsive design** — Works on desktop and mobile

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + native WebSockets |
| Frontend | Jinja2 templates, vanilla JS, KaTeX |
| Diagrams | SVG (generated server-side in Python) |
| Styling | Custom CSS, responsive grid/flexbox |

## Quick Start

### 1. Install dependencies

```bash
uv pip install -r requirements.txt
```

Or with pip:

```bash
pip install -r requirements.txt
```

### 2. Run the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Or:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Play

Open `http://localhost:8000` in your browser.

1. Enter your name and create a room (or join with a room code)
2. Invite friends by sharing the room code
3. The host clicks **Start Game**
4. Solve polygon problems as fast as you can!

## Game Rules

- Each game has a configurable number of rounds (default: 10)
- You have a limited time per question (default: 20 seconds)
- Correct answers earn **100 base points**
- **Speed bonus**: up to +200 points for lightning-fast answers
- **Streak bonus**: +10 per consecutive correct answer (max +50)
- The player with the highest score at the end wins

## Problem Types

1. **Missing angle in a triangle/quadrilateral** — Calculate the unknown angle
2. **Regular polygon interior angle** — Find each interior angle of a regular polygon
3. **Exterior angle** — Find each exterior angle of a regular polygon
4. **Angle sum** — Find the sum of interior angles (or find sides from the sum)
5. **Polygon name** — Identify the polygon from its angle properties
6. **Sides from angle** — Find the number of sides given the interior angle

## Project Structure

```
interactive-math/
├── main.py              # FastAPI app, HTTP routes, WebSocket handler
├── requirements.txt     # Python dependencies
├── game/
│   ├── manager.py       # Room & game state management
│   ├── generator.py     # Problem generator
│   └── renderer.py      # SVG polygon diagram builder
├── static/
│   ├── css/style.css    # Styles
│   └── js/game.js       # WebSocket client & game UI
└── templates/
    ├── base.html        # Base layout with KaTeX
    ├── index.html       # Landing page
    └── room.html        # Lobby + game + results
```
