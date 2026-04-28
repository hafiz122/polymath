"""Real-time game room manager with asyncio-safe state."""
import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from fastapi import WebSocket

from game.generator import Problem, generate_problem


@dataclass
class Player:
    id: str
    name: str
    websocket: Optional[WebSocket] = None
    score: int = 0
    streak: int = 0
    connected: bool = True
    answered_current: bool = False
    answer_time_ms: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "score": self.score,
            "streak": self.streak,
            "connected": self.connected,
            "answered_current": self.answered_current,
        }


@dataclass
class RoomSettings:
    rounds: int = 10
    time_per_question: int = 20  # seconds
    difficulty: int = 1
    use_timer: bool = True
    topics: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "rounds": self.rounds,
            "time_per_question": self.time_per_question,
            "difficulty": self.difficulty,
            "use_timer": self.use_timer,
            "topics": self.topics,
        }


@dataclass
class Room:
    id: str
    host_id: str
    players: Dict[str, Player] = field(default_factory=dict)
    status: str = "waiting"  # waiting, playing, finished
    settings: RoomSettings = field(default_factory=RoomSettings)
    current_round: int = 0
    current_problem: Optional[Problem] = None
    round_start_time: Optional[float] = None
    scores_history: List[dict] = field(default_factory=list)
    timer_task: Optional[asyncio.Task] = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "host_id": self.host_id,
            "status": self.status,
            "settings": self.settings.to_dict(),
            "current_round": self.current_round,
            "players": [p.to_dict() for p in self.players.values()],
        }

    def leaderboard(self) -> List[dict]:
        return sorted(
            [p.to_dict() for p in self.players.values()],
            key=lambda x: (-x["score"], x["name"]),
        )


class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self._lock = asyncio.Lock()

    async def create_room(self, host_name: str, settings: Optional[dict] = None) -> Room:
        room_id = str(uuid.uuid4())[:8].upper()
        host_id = str(uuid.uuid4())
        room_settings = RoomSettings()
        if settings:
            room_settings.rounds = settings.get("rounds", 10)
            room_settings.time_per_question = settings.get("time_per_question", 20)
            room_settings.difficulty = settings.get("difficulty", 1)
            room_settings.use_timer = settings.get("use_timer", True)
            room_settings.topics = settings.get("topics", [])

        room = Room(
            id=room_id,
            host_id=host_id,
            settings=room_settings,
        )
        host = Player(id=host_id, name=host_name)
        room.players[host_id] = host

        async with self._lock:
            self.rooms[room_id] = room
        return room

    async def join_room(self, room_id: str, player_name: str) -> Optional[tuple]:
        room_id = room_id.upper()
        async with self._lock:
            room = self.rooms.get(room_id)
            if not room:
                return None
            if room.status != "waiting":
                return None
            if len(room.players) >= 8:
                return None

        player_id = str(uuid.uuid4())
        player = Player(id=player_id, name=player_name)

        async with room.lock:
            room.players[player_id] = player

        await self.broadcast(room_id, {
            "type": "player_joined",
            "player": player.to_dict(),
            "room": room.to_dict(),
        })
        return player_id, room

    async def connect_player(self, room_id: str, player_id: str, websocket: WebSocket):
        room_id = room_id.upper()
        room = self.rooms.get(room_id)
        if not room:
            return False
        async with room.lock:
            player = room.players.get(player_id)
            if not player:
                return False
            player.websocket = websocket
            player.connected = True
        return True

    async def disconnect_player(self, room_id: str, player_id: str):
        room_id = room_id.upper()
        room = self.rooms.get(room_id)
        if not room:
            return
        async with room.lock:
            player = room.players.get(player_id)
            if player:
                player.websocket = None
                player.connected = False

        await self.broadcast(room_id, {
            "type": "player_left",
            "player_id": player_id,
            "room": room.to_dict(),
        })

        # Clean up empty rooms after a delay
        if all(not p.connected for p in room.players.values()):
            asyncio.create_task(self._cleanup_room(room_id, delay=60))

    async def _cleanup_room(self, room_id: str, delay: int = 60):
        await asyncio.sleep(delay)
        room = self.rooms.get(room_id)
        if room and all(not p.connected for p in room.players.values()):
            async with self._lock:
                self.rooms.pop(room_id, None)

    async def start_game(self, room_id: str, player_id: str) -> bool:
        room_id = room_id.upper()
        room = self.rooms.get(room_id)
        if not room:
            return False
        async with room.lock:
            if room.host_id != player_id:
                return False
            if room.status != "waiting":
                return False
            if len(room.players) < 1:
                return False
            room.status = "playing"
            room.current_round = 0
            for p in room.players.values():
                p.score = 0
                p.streak = 0

        await self.broadcast(room_id, {
            "type": "game_started",
            "room": room.to_dict(),
        })
        await asyncio.sleep(1)
        await self._start_round(room_id)
        return True

    async def _start_round(self, room_id: str):
        room = self.rooms.get(room_id)
        if not room:
            return

        async with room.lock:
            if room.status != "playing":
                return
            room.current_round += 1
            if room.current_round > room.settings.rounds:
                room.status = "finished"
                await self.broadcast(room_id, {
                    "type": "game_finished",
                    "leaderboard": room.leaderboard(),
                    "room": room.to_dict(),
                })
                return

            for p in room.players.values():
                p.answered_current = False
                p.answer_time_ms = None

            problem = generate_problem(
                difficulty=room.settings.difficulty,
                topics=room.settings.topics or None,
            )
            room.current_problem = problem
            room.round_start_time = time.time()

        await self.broadcast(room_id, {
            "type": "round_started",
            "round": room.current_round,
            "total_rounds": room.settings.rounds,
            "problem": {
                "question": problem.question,
                "question_latex": problem.question_latex,
                "svg_markup": problem.svg_markup,
                "options": problem.options,
            },
            "time_limit": room.settings.time_per_question,
            "use_timer": room.settings.use_timer,
        })

        # Start timer task only if timer is enabled
        if room.settings.use_timer:
            if room.timer_task:
                room.timer_task.cancel()
            room.timer_task = asyncio.create_task(
                self._round_timer(room_id, room.settings.time_per_question)
            )

    async def _round_timer(self, room_id: str, duration: int):
        await asyncio.sleep(duration)
        await self._end_round(room_id)

    async def _end_round(self, room_id: str):
        room = self.rooms.get(room_id)
        if not room:
            return

        problem = room.current_problem
        explanation = problem.explanation if problem else ""

        await self.broadcast(room_id, {
            "type": "round_ended",
            "correct_answer": problem.correct_answer if problem else "",
            "explanation": explanation,
            "leaderboard": room.leaderboard(),
        })

        await asyncio.sleep(4)  # Show explanation before next round
        await self._start_round(room_id)

    async def submit_answer(self, room_id: str, player_id: str, answer: str) -> dict:
        room_id = room_id.upper()
        room = self.rooms.get(room_id)
        if not room:
            return {"error": "Room not found"}

        async with room.lock:
            player = room.players.get(player_id)
            if not player or player.answered_current:
                return {"error": "Already answered"}

            problem = room.current_problem
            if not problem or room.status != "playing":
                return {"error": "No active problem"}

            player.answered_current = True
            is_correct = answer.strip() == problem.correct_answer.strip()
            elapsed_ms = int((time.time() - room.round_start_time) * 1000) if room.round_start_time else 0
            player.answer_time_ms = elapsed_ms

            if is_correct:
                # Scoring: base 100 + speed bonus (only if timer on) + streak bonus
                speed_bonus = 0
                if room.settings.use_timer:
                    speed_bonus = max(0, int((room.settings.time_per_question * 1000 - elapsed_ms) / 100))
                player.streak += 1
                streak_bonus = min(player.streak * 10, 50)
                points = 100 + speed_bonus + streak_bonus
                player.score += points
            else:
                player.streak = 0
                points = 0

            # Check if all players answered
            all_answered = all(p.answered_current or not p.connected for p in room.players.values())

        result = {
            "type": "answer_result",
            "player_id": player_id,
            "correct": is_correct,
            "points": points,
            "streak": player.streak,
            "total_score": player.score,
            "time_ms": elapsed_ms,
            "correct_answer": problem.correct_answer,
        }

        await self.broadcast(room_id, result)

        if all_answered:
            if room.timer_task:
                room.timer_task.cancel()
                room.timer_task = None
            await self._end_round(room_id)

        return result

    async def broadcast(self, room_id: str, message: dict):
        room_id = room_id.upper()
        room = self.rooms.get(room_id)
        if not room:
            return
        disconnected = []
        for player in room.players.values():
            if player.websocket and player.connected:
                try:
                    await player.websocket.send_json(message)
                except Exception:
                    disconnected.append(player.id)
        for pid in disconnected:
            await self.disconnect_player(room_id, pid)

    def get_room(self, room_id: str) -> Optional[Room]:
        return self.rooms.get(room_id.upper())


# Singleton manager instance
manager = RoomManager()
