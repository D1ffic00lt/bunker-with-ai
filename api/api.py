import json
import os.path
import random
import re
import httpx

from fastapi import FastAPI, HTTPException, Request, WebSocketException, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket
from sqlalchemy import select, delete, and_

from database.db_session import create_session, global_init
from database.rooms import Room
from database.users import User
from database.auth import Auth
from manager import WebSocketManager, WebSocketConnection

app = FastAPI()
reg = re.compile("\"(.*?)\"")
manager = WebSocketManager()


@app.on_event("startup")
async def setup_resources():
    if not os.path.isdir("./.database/"):
        os.mkdir("./.database/")
    await global_init("./.database/games.db")


def get_game_code(num_chars) -> str:
    code_chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    code = ''
    for i in range(0, num_chars):
        slice_start = random.randint(0, len(code_chars) - 1)
        code += code_chars[slice_start: slice_start + 1]
    return code


@app.websocket("/bunker/api/v1/ws/{game_code}")
async def websocket_endpoint(websocket: WebSocket, game_code: str):
    websocket = WebSocketConnection(websocket, game_code)
    await manager.connect(websocket, game_code)
    try:
        while True:
            await websocket.receive_json()
    except (WebSocketException, WebSocketDisconnect):
        await manager.disconnect(websocket, game_code)


@app.post('/bunker/api/v1/new-game/{user_id}')
async def new_game(user_id: int):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(select(Room).where(Room.host_id == user_id))
            room_id = room_id.scalars().all()
            await session.execute(delete(Room).where(Room.host_id == user_id))
            for i in room_id:
                await session.execute(delete(User).where(User.room_id == int(i.id)))
    async with httpx.AsyncClient() as client:
        try:
            cat = await client.post(
                "http://generator:4322/generator/api/v1/catastrophe",
                timeout=120, follow_redirects=True
            )
            if cat.status_code // 100 in [5, 4]:
                if 'application/json' in cat.headers.get('Content-Type', ''):
                    return JSONResponse(
                        content={"status": False, "error": cat.json().get("error", None)},
                        status_code=cat.status_code
                    )
                return JSONResponse(content={"status": False})
            cat = cat.json()
            bunker = await client.post("http://generator:4322/generator/api/v1/bunker", timeout=120)
            if bunker.status_code // 100 in [5, 4]:
                if 'application/json' in bunker.headers.get('Content-Type', ''):
                    return JSONResponse(
                        content={"status": True, "error": bunker.json().get("error", None)},
                        status_code=bunker.status_code
                    )
                return JSONResponse(content={"status": False})
            bunker = bunker.json()
        except httpx.TimeoutException:
            raise HTTPException(status_code=501, detail="Превышено время ожидания запроса.")
        except (KeyError, json.decoder.JSONDecodeError):
            raise HTTPException(status_code=501, detail="Ошибка обработки данных.")
    async with create_session() as session:
        async with session.begin():
            new_room = Room()
            new_room.host_id = user_id
            new_room.bunker = bunker["desc"]
            new_room.threat = bunker["threat"]
            new_room.catastrophe = cat["desc"]
            new_room.game_code = get_game_code(32)
            session.add(new_room)
            return JSONResponse(
                content={
                    "room": new_room.game_code, "catastrophe": new_room.catastrophe,
                    "bunker": new_room.bunker, "threat": new_room.threat
                }, status_code=201
            )


@app.post('/bunker/api/v1/remove-room/{game_code}')
async def remove_room(game_code: str):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return JSONResponse(
                    content={"status": False, "error": "Комната не найдена."},
                    status_code=404
                )
            await session.execute(
                delete(Room).where(Room.game_code == game_code)
            )
            await session.execute(
                delete(User).where(User.room_id == int(room_id))
            )
    await manager.remove_connection(game_code)
    return JSONResponse(content={"status": True})


@app.get("/bunker/api/v1/game-code/{host_id}")
async def get_game_code_id(host_id: int):
    async with create_session() as session:
        async with session.begin():
            room = await session.execute(
                select(Room).where(Room.host_id == host_id)
            )
            room = room.scalars().first()
            if room is None:
                return JSONResponse(
                    content={"status": False, "error": "Комната не найдена."},
                    status_code=404
                )
            return JSONResponse(content={"game_code": room.game_code})


@app.patch("/bunker/api/v1/reveal-characteristic/{game_code}/{user_id}")
async def reveal_characteristic(game_code: str, user_id: int, request: Request):
    request = await request.json()
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return JSONResponse(
                    content={"status": False, "error": "Комната не найдена."},
                    status_code=404
                )

            user = await session.execute(
                select(User).where(and_(User.room_id == room_id.id, User.user_id == user_id))
            )
            user = user.scalars().first()
            if user is None:
                return JSONResponse(
                    content={"status": False, "error": "Пользователь не найден."},
                    status_code=404
                )

            user.update(request["attribute"] + "_revealed")
            await manager.send_message(
                game_code, {
                    "type": "reveal_characteristic",
                    "user_id": user_id,
                }
            )
            await session.commit()
    return JSONResponse(content={"status": True}, status_code=201)


@app.patch('/bunker/api/v1/leave-game/{game_code}/{user_id}')
async def leave_game(game_code: str, user_id: int):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return JSONResponse({"status": False, "error": "Комната не найдена."}, 404)

            user = await session.execute(
                select(User).where(and_(User.room_id == room_id.id, User.user_id == user_id))
            )
            user = user.scalars().first()
            user.leave()
            await manager.send_message(
                game_code, {
                    "type": "leave_game",
                    "user_id": user_id
                }
            )
            await session.commit()
    return JSONResponse(content={"status": True}, status_code=201)


@app.post('/bunker/api/v1/use-active-card/{game_code}/{user_id}')
async def use_active_card(game_code: str, user_id: int, request: Request):
    request = await request.json()
    async with create_session() as session:
        async with session.begin():
            room = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room = room.scalars().first()
            room_id = room.id
            if room_id is None:
                return JSONResponse(
                    content={"status": False, "error": "Комната не найдена."},
                    status_code=404
                )

            user = await session.execute(
                select(User).where(
                    and_(User.room_id == room_id, User.user_id == user_id)
                )
            )
            user = user.scalars().first()
            active_card = user.action_card
    try:
        async with httpx.AsyncClient() as client:
            active_card = await client.get(
                f"http://generator:4322/generator/api/v1/get-active-card/{active_card}"
            )
            active_card = active_card.json()
    except httpx.TimeoutException:
        return JSONResponse(
            content={"status": False, "error": "Превышено время ожидания запроса."},
            status_code=404
        )
    if not request.json["switch"] and active_card["id"] in [2, 6]:
        return JSONResponse(content={"status": False}, status_code=424)
    async with create_session() as session:
        async with session.begin():
            if active_card["id"] == 3:
                player_card_attr = reg.findall(active_card["card"])[0]
                users = await session.execute(
                    select(User).where(
                        and_(User.get_attr(player_card_attr, revealed=True), User.active, User.room_id == room_id)
                    )
                )
                users = users.scalars().all()
                player = None
                for i in users:
                    if i.user_id == user_id:
                        player = i
                users = list(filter(lambda x: x.user_id != user_id, users))
                if not users or player is None:
                    return JSONResponse(
                        content={"status": False, "error": "Игрок не найден."},
                        status_code=404
                    )
                player_to_switch = random.choice(users)
                attr = player_to_switch.get_attr(player_card_attr)

                player_to_switch.set_attr(player_card_attr, player.get_attr(player_card_attr))
                player.set_attr(player_card_attr, attr)
                player_to_switch.switches += 1
                player.switches += 1
                await manager.send_message(
                    game_code, {
                        "type": "use_active_card",
                        "user_id": player.user_id
                    }
                )
                await manager.send_message(
                    game_code, {
                        "type": "use_active_card",
                        "user_id": player_to_switch.user_id
                    }
                )
            elif active_card["id"] == 5:
                player_card_attr = reg.findall(active_card["card"])[0]
                users = await session.execute(
                    select(User).where(
                        and_(User.get_attr(player_card_attr, revealed=True), User.active, User.room_id == room_id)
                    )
                )
                users = users.scalars().all()
                attrs = [i.get_attr(player_card_attr) for i in users]
                random.shuffle(attrs)
                for i in range(len(users)):
                    users[i].set_attr(player_card_attr, attrs[i])
                    users[i].switches += 1
                    await manager.send_message(
                        game_code, {
                            "type": "use_active_card",
                            "user_id": users[i].user_id
                        }
                    )
            elif active_card["id"] == 7:
                user.health = "Здоров 100%"
                user.switches += 1
                await manager.send_message(
                    game_code, {
                        "type": "use_active_card",
                        "user_id": user_id
                    }
                )
            elif active_card["id"] == 11:
                room.additional_information += "дружественный бункер неподалёку; "
            elif active_card["id"] == 12:
                room.additional_information += "враждебный бункер неподалёку; "
            elif active_card["id"] == 13:
                room.additional_information += "заброшенная больница неподалёку; "
            elif active_card["id"] == 14:
                room.additional_information += "заброшенный военный лагерь неподалёку; "
            elif active_card["id"] == 2:
                data = request.json  # {user_id: ...}
                player_card_attr = reg.findall(active_card["card"])[0]
                users = await session.execute(
                    select(User).where(
                        and_(User.get_attr(player_card_attr, revealed=True), User.active, User.room_id == room_id)
                    )
                )
                users = users.scalars().all()
                player = None
                player_to_switch = None
                for i in users:
                    if i.user_id == user_id:
                        player = i
                    if i.user_id == int(data["user_id"]):
                        player_to_switch = i
                users = list(filter(lambda x: x.user_id != user_id, users))

                if not users or player is None or player_to_switch is None:
                    return JSONResponse(
                        content={"status": False, "error": "Игрок не найден."},
                        status_code=404
                    )
                attr = player_to_switch.get_attr(player_card_attr)

                player_to_switch.set_attr(player_card_attr, player.get_attr(player_card_attr))
                player.set_attr(player_card_attr, attr)
                player_to_switch.switches += 1
                player.switches += 1
                await manager.send_message(
                    game_code, {
                        "type": "use_active_card",
                        "user_id": player.user_id
                    }
                )
                await manager.send_message(
                    game_code, {
                        "type": "use_active_card",
                        "user_id": player_to_switch.user_id
                    }
                )
            elif active_card["id"] == 6:
                data = request.json
                player_to_switch = None
                users = await session.execute(select(User).where(and_(User.active, User.room_id == room_id)))
                users = users.scalars().all()
                for i in users:
                    if i.user_id == int(data["user_id"]):
                        player_to_switch = i
                        break
                users = list(filter(lambda x: x.user_id != user_id, users))
                if not users or player_to_switch is None:
                    return JSONResponse(
                        content={"status": False, "error": "Игрок не найден."},
                        status_code=404
                    )

                player_to_switch.set_attr("Здоровье", "Здоров 100%")
                player_to_switch.switches += 1
                await manager.send_message(
                    game_code, {
                        "type": "use_active_card",
                        "user_id": player_to_switch.user_id
                    }
                )
            await session.commit()
            return KeyError({"status": True}, 201)


@app.post("/bunker/api/v1/start-game/{game_code}")
async def start_game(game_code: str):
    async with create_session() as session:
        async with session.begin():
            room = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room = room.scalars().first()
            if room is None:
                return JSONResponse(
                    content={"status": False, "error": "Комната не найдена"},
                    status_code=404
                )
            room.started = True
            await session.commit()
            return JSONResponse(
                content={"status": True},
                status_code=201
            )


@app.post('/bunker/api/v1/add-user/{game_code}/{user_id}')
async def add_user(game_code: str, user_id: int):
    async with create_session() as session:
        async with session.begin():
            await session.execute(delete(User).where(User.user_id == user_id))
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return JSONResponse(
                    content={"status": False, "error": "Комната не найдена."},
                    status_code=404
                )
            if room_id.started:
                return JSONResponse(
                    content={"status": False, "error": "Игра уже идёт."},
                    status_code=400
                )
            room_id = room_id.id
    try:
        async with httpx.AsyncClient() as client:
            user_data = await client.post(
                f"http://generator:4322/generator/api/v1/player/{game_code}", timeout=120
            )
            if user_data.status_code // 100 in [5, 4]:
                if 'application/json' in user_data.headers.get('Content-Type', ''):
                    return JSONResponse(
                        content={"status": True, "error": user_data.json().get("error", None)},
                        status_code=user_data.status_code
                    )
                return JSONResponse({"status": False})
            user_data = user_data.json()
    except httpx.TimeoutException:
        return JSONResponse(content={"status": False, "error": "Превышено время ожидания запроса."}, status_code=501)
    except (KeyError, json.decoder.JSONDecodeError):
        return JSONResponse(content={"status": False}, status_code=501)
    async with create_session() as session:
        async with session.begin():
            user = User()
            user.user_id = user_id
            user.age = user_data["age"]
            user.fact1 = user_data["fact1"]
            user.fact2 = user_data["fact2"]
            user.action_card = user_data["action_card"]
            user.phobia = user_data["phobia"]
            user.health = user_data["health"]
            user.luggage = user_data["luggage"]
            user.hobby = user_data["hobby"]
            user.profession = user_data["profession"]
            user.gender = user_data["gender"]
            user.room_id = room_id
            session.add(user)
            try:
                json_data = user.to_json()
            except (KeyError, json.decoder.JSONDecodeError):
                return JSONResponse(content={"status": False}, status_code=501)
            json_data["status"] = True
            return JSONResponse(content=json_data, status_code=201)


@app.post("/bunker/api/v1/result/bunker")
async def bunker_result(request: Request):
    request = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            result = await client.post(
                f"http://generator:4322/generator/api/v1/bunker-result",
                json=request.json,
                timeout=120
            )
        except httpx.TimeoutException:
            return JSONResponse(
                content={"status": False, "error": "Превышено время ожидания запроса."},
                status_code=501
            )
        if result.status_code // 100 in [5, 4]:
            if 'application/json' in result.headers.get('Content-Type', ''):
                return JSONResponse(
                    content={"status": True, "error": result.json().get("error", None)},
                    status_code=result.status_code
                )
            return JSONResponse(content={"status": False}, status_code=501)
        result = result.json()
    await manager.remove_all_connections(request.json["game_code"])
    return JSONResponse(content=result, status_code=201)


@app.put("/bunker/api/v1/user/add-vote/{game_code}/{user_id}")
async def add_vote(game_code: str, user_id: int):

    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return JSONResponse(content={"status": False, "error": "Комната не найдена"}, status_code=404)

            user = await session.execute(
                select(User).where(and_(User.room_id == room_id.id, User.user_id == user_id))
            )
            user = user.scalars().first()
            if user is None:
                return JSONResponse(content={"status": False, "error": "Игрок не найден"}, status_code=404)

            user.number_of_votes += 1
            await manager.send_message(
                game_code, {
                    "type": "add_vote",
                    "user_id": user_id
                }
            )
            return JSONResponse(content={"status": True}, status_code=201)


@app.put("/bunker/api/v1/user/remove-vote/{game_code}/{user_id}")
async def remove_vote(game_code: str, user_id: int):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return JSONResponse(content={"status": False, "error": "Комната не найдена"}, status_code=404)

            user = await session.execute(
                select(User).where(and_(User.room_id == room_id.id, User.user_id == user_id))
            )
            user = user.scalars().first()
            if user is None:
                return JSONResponse(content={"status": False, "error": "Игрок не найден."}, status_code=404)

            user.number_of_votes -= 1
            await manager.send_message(
                game_code, {
                    "type": "remove_vote",
                    "user_id": user_id
                }
            )
            return JSONResponse(content={"status": True}, status_code=201)


@app.put("/bunker/api/v1/user/reset-vote/{game_code}")
async def reset_vote(game_code: str):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return JSONResponse(content={"status": False, "error": "Комната не найдена."}, status_code=404)

            users = await session.execute(
                select(User).where(User.room_id == int(room_id.id))
            )
            users = users.scalars().all()
            if users is None:
                return JSONResponse(content={"status": False, "error": "Игроки не найдены."}, status_code=404)

            for user in users:
                user.number_of_votes = 0
                await manager.send_message(
                    game_code, {
                        "type": "reset_vote",
                        "user_id": user.user_id
                    }
                )

            return JSONResponse(content={"status": True}, status_code=201)


@app.post("/bunker/api/v1/result/surface")
async def surface_result(request: Request):
    request = await request.json()
    async with httpx.AsyncClient() as client:
        try:
            result = await client.post(
                f"http://generator:4322/generator/api/v1/result",
                json=request.json,
                timeout=120
            )
        except httpx.TimeoutException:
            return JSONResponse(
                content={"status": False, "error": "Превышено время ожидания запроса."}, status_code=501
            )
        if result.status_code // 100 in [5, 4]:
            if 'application/json' in result.headers.get('Content-Type', ''):
                return JSONResponse(
                    content={"status": True, "error": result.json().get("error", None)},
                    status_code=result.status_code
                )
            return JSONResponse(content={"status": False}, status_code=501)
        result = result.json()
    return JSONResponse(content=result, status_code=201)


@app.get("/bunker/api/v1/get-game/{game_code}")
async def get_game(game_code: str):
    response = {}
    async with create_session() as session:
        async with session.begin():
            room = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room = room.scalars().first()
            if room is None:
                return JSONResponse(content={"status": False, "error": "Комната не найдена."}, status_code=404)

            response["id"] = room.id
            response["host_id"] = room.host_id
            response["game_code"] = room.game_code
            response["bunker"] = room.bunker
            response["threat"] = room.threat
            response["catastrophe"] = room.catastrophe
            response["started"] = room.started
            response["additional_information"] = room.additional_information
            response["users"] = []
            users = await session.execute(
                select(User).where(User.room_id == int(room.id))
            )
            users = users.scalars().all()

            for i in users:
                response["users"].append(
                    i.to_json()
                )

            return JSONResponse(content=response, status_code=200)


@app.post("/bunker/api/v1/auth")
async def auth_user_post(request: Request):
    request = request.query_params
    token_hash = request.get("token_hash", None)
    user_id = request.get("user_id", None)
    expiration_date = request.get("expiration_date", None)
    if token_hash is None:
        async with create_session() as session:
            async with session.begin():
                auth = Auth()
                token = auth.generate_token()
                auth.token_hash = auth.hash(token)
                if expiration_date is not None:
                    auth.expiration_date = expiration_date

                session.add(auth)
                await session.commit()
                response = {
                    "token": token
                }
                return JSONResponse(content=response, status_code=201)

    async with create_session() as session:
        async with session.begin():
            auth = await session.execute(
                select(Auth).where(Auth.token_hash == token_hash)
            )
            auth = auth.scalars().first()
            if auth is None:
                response = {
                    "auth": False,
                    "message": "Token not found.",
                    "error": "Token not found."
                }
                return JSONResponse(response, status_code=404)
            message, code = auth.auth(int(user_id))
            return JSONResponse(content=message, status_code=code)


@app.get("/bunker/api/v1/auth")
async def auth_user():
    async with create_session() as session:
        async with session.begin():
            users = await session.execute(
                select(Auth).where(
                    and_(Auth.user_id.isnot(None))
                )
            )
            users = users.scalars().all()
            users = list(filter(lambda x: x.expiration(), users))
            return JSONResponse(content=list(map(lambda x: x.get_main_info(), users)), status_code=200)
