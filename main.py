"""FastAPI app for Polygon Speed Math Game."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from game.manager import manager

app = FastAPI(title="Polygon Speed Math")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse(request, "pricing.html")


@app.get("/modes", response_class=HTMLResponse)
async def modes(request: Request):
    return templates.TemplateResponse(request, "modes.html")


@app.post("/create-room")
async def create_room(
    request: Request,
    player_name: str = Form(...),
    rounds: int = Form(10),
    time_per_question: int = Form(20),
    difficulty: int = Form(1),
    use_timer: bool = Form(True),
):
    settings = {
        "rounds": rounds,
        "time_per_question": time_per_question,
        "difficulty": difficulty,
        "use_timer": use_timer,
    }
    room = await manager.create_room(player_name, settings)
    player = room.players[room.host_id]
    response = RedirectResponse(url=f"/room/{room.id}", status_code=303)
    response.set_cookie(key="player_id", value=player.id, max_age=3600)
    response.set_cookie(key="player_name", value=player.name, max_age=3600)
    return response


@app.post("/join-room")
async def join_room(
    request: Request,
    player_name: str = Form(...),
    room_code: str = Form(...),
):
    result = await manager.join_room(room_code, player_name)
    if not result:
        return templates.TemplateResponse(
            request,
            "index.html",
            {"error": "Invalid room code or game already started."},
        )
    player_id, room = result
    response = RedirectResponse(url=f"/room/{room.id}", status_code=303)
    response.set_cookie(key="player_id", value=player_id, max_age=3600)
    response.set_cookie(key="player_name", value=player_name, max_age=3600)
    return response


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def room_page(request: Request, room_id: str):
    room = manager.get_room(room_id)
    if not room:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "room.html", {"room_id": room_id})


@app.websocket("/ws/rooms/{room_id}")
async def websocket_room(websocket: WebSocket, room_id: str):
    await websocket.accept()
    player_id = websocket.cookies.get("player_id")
    player_name = websocket.cookies.get("player_name")

    if not player_id or not player_name:
        await websocket.send_json({"type": "error", "message": "Missing player info."})
        await websocket.close()
        return

    connected = await manager.connect_player(room_id, player_id, websocket)
    if not connected:
        await websocket.send_json({"type": "error", "message": "Room not found or player not in room."})
        await websocket.close()
        return

    # Send current room state
    room = manager.get_room(room_id)
    if room:
        await websocket.send_json({
            "type": "room_state",
            "room": room.to_dict(),
            "you": player_id,
        })

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")

            if action == "start_game":
                await manager.start_game(room_id, player_id)
            elif action == "submit_answer":
                answer = data.get("answer", "")
                await manager.submit_answer(room_id, player_id, answer)
            elif action == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await manager.disconnect_player(room_id, player_id)
    except Exception as e:
        await manager.disconnect_player(room_id, player_id)


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
