import asyncio
import base64
import io
import httpx
import json

from copy import deepcopy
from functools import lru_cache
from websocket import create_connection, WebSocket
from fastapi import WebSocket as FastAPIWebSocket
from collections import defaultdict

NOT_FOUND_FRAME_DATA = {
    "gender_revealed": False,
    "age_revealed": False,
    "profession_revealed": False,
    "health_revealed": False,
    "luggage_revealed": False,
    "fact1_revealed": False,
    "fact2_revealed": False,
    "phobia_revealed": False,
    "hobby_revealed": False,
    "number_of_votes": 0,
    "active": True
}


def cache(async_function):
    @lru_cache
    def wrapper(*args, **kwargs):
        coroutine = async_function(*args, **kwargs)
        return asyncio.ensure_future(coroutine)

    return wrapper


# @cache
async def get_not_found_frame():
    async with httpx.AsyncClient() as requests:
        try:
            raw_not_found_frame = await requests.post(
                "http://frame-generator:1334/api/v1/get-user-frame", json=NOT_FOUND_FRAME_DATA
            )
        except httpx.TimeoutException:
            return b""
        if raw_not_found_frame.status_code // 100 in [4, 5]:
            return b""

        raw_not_found_frame = raw_not_found_frame.content
        raw_not_found_frame = base64.b64encode(io.BytesIO(raw_not_found_frame).getvalue()).decode('utf-8')

        return raw_not_found_frame


class Connection(object):
    PORT = 9462
    URL = "ws://api:{port}/bunker/api/v1/ws/{game_code}"

    def __init__(self, game_code):
        self.game_code = game_code
        self.ws: WebSocket = create_connection(
            self.URL.format(port=self.PORT, game_code=self.game_code)
        )

    def recv(self):
        return self.ws.recv()

    def close(self):
        return self.ws.close()


class Manager(object):
    def __init__(self, frame_manager: "FrameStreamManager"):
        self.frame_manager = frame_manager
        self.connections: dict[str, Connection] = {}
        self.tasks: set[asyncio.Task] = set()

    def close(self, game_code):
        if self.connections.get(game_code):
            self.connections[game_code].close()
            del self.connections[game_code]

    def create_connection(self, game_code) -> Connection:
        connection = Connection(game_code)
        self.connections[game_code] = connection
        return connection

    def exists(self, game_code: str) -> bool:
        return game_code in self.connections

    def wait_for_update(self, game_code):
        task = asyncio.create_task(self._wait_for_update(game_code))
        self.tasks.add(task)
        task.add_done_callback(lambda _: self.tasks.remove(task))

    async def _wait_for_update(self, game_code):
        # TODO: not-found -> func
        while True:
            try:
                message = json.loads(self.connections[game_code].recv())
                self.connections[game_code].ws.pong()
                if not message.get("user_id"):
                    continue
                connected_user: WebSocketConnection | None = None
                for connection in self.frame_manager.active_connections[game_code]:
                    if connection.user_id == message["user_id"]:
                        connected_user = connection
                        break
                if not connected_user:
                    continue
                async with httpx.AsyncClient() as requests:
                    game = await requests.get(
                        "http://api:9462/bunker/api/v1/get-game/{}".format(game_code),
                        timeout=60
                    )
                    if game.status_code // 100 in [4, 5]:
                        frame = await get_not_found_frame()
                        await connected_user.send_text(frame)
                        continue

                    game = game.json()
                    user_data = {}
                    for user in game["users"]:
                        if user["user_id"] == connected_user.user_id:
                            user_data = deepcopy(user)
                            break
                    if user_data == {}:
                        frame = await get_not_found_frame()
                        await connected_user.send_text(frame)
                        continue
                    frame = await requests.post(
                        "http://frame-generator:1334/api/v1/get-user-frame", json=user_data
                    )
                    if frame.status_code // 100 in [4, 5]:
                        frame = await get_not_found_frame()
                        await connected_user.send_text(frame)
                        continue
                    frame = frame.content
                    frame = base64.b64encode(io.BytesIO(frame).getvalue()).decode('utf-8')
                    await connected_user.send_text(frame)
            except Exception as e:
                print(f"Error during waiting for update: {e}")
                self.close(game_code)
                break


class WebSocketConnection(object):
    def __init__(self, websocket: FastAPIWebSocket, game_code: str, user_id: int):
        self.websocket = websocket
        self.game_code = game_code
        self.user_id = user_id

    async def accept(self):
        return await self.websocket.accept()

    async def send_text(self, message: str):
        await self.websocket.send_text(message)

    async def receive(self):
        return await self.websocket.receive()

    async def close(self):
        return await self.websocket.close()


class FrameStreamManager(object):
    def __init__(self):
        self.active_connections: dict[str, list[WebSocketConnection]] = defaultdict(list)
