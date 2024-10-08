import asyncio
import json
import os.path
import random
import re
import httpx

from flask import Flask, make_response, jsonify, request
from sqlalchemy import select, delete, and_

from database.db_session import create_session, global_init
from database.rooms import Room
from database.users import User
from database.auth import Auth

app = Flask(__name__)

if not os.path.isdir("./.database/"):
    os.mkdir("./.database/")
asyncio.run(global_init("./.database/games.db"))
reg = re.compile("\"(.*?)\"")


def get_game_code(num_chars) -> str:
    code_chars = '0123456789abcdefghijklmnopqrstuvwxyz'
    code = ''
    for i in range(0, num_chars):
        slice_start = random.randint(0, len(code_chars) - 1)
        code += code_chars[slice_start: slice_start + 1]
    return code


@app.route('/bunker/api/v1/new-game/<int:user_id>', methods=['POST'])
async def new_game(user_id):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(select(Room).where(Room.host_id == user_id))
            room_id = room_id.scalars().all()
            await session.execute(delete(Room).where(Room.host_id == user_id))
            for i in room_id:
                await session.execute(delete(User).where(User.room_id == i.id))
    async with httpx.AsyncClient() as client:
        try:
            cat = await client.post(
                "http://generator:4322/generator/api/v1/catastrophe",
                timeout=120, follow_redirects=True
            )
            if cat.status_code // 100 in [5, 4]:
                if 'application/json' in cat.headers.get('Content-Type', ''):
                    return make_response(jsonify(
                        {"status": True, "error": cat.json().get("error", None)}
                    ), cat.status_code)
                return make_response({"status": False})
            cat = cat.json()
            bunker = await client.post("http://generator:4322/generator/api/v1/bunker", timeout=120)
            if bunker.status_code // 100 in [5, 4]:
                if 'application/json' in bunker.headers.get('Content-Type', ''):
                    return make_response(jsonify(
                        {"status": True, "error": bunker.json().get("error", None)}
                    ), bunker.status_code)
                return make_response({"status": False})
            bunker = bunker.json()
        except httpx.TimeoutException:
            return make_response(jsonify({"status": False, "error": "Превышено время ожидания запроса."}), 501)
        except (KeyError, json.decoder.JSONDecodeError):
            return make_response(jsonify({"status": False}), 501)
    async with create_session() as session:
        async with session.begin():
            new_room = Room()
            new_room.host_id = user_id
            new_room.bunker = bunker["desc"]
            new_room.threat = bunker["threat"]
            new_room.catastrophe = cat["desc"]
            new_room.game_code = get_game_code(32)
            session.add(new_room)
            return make_response(jsonify({
                "room": new_room.game_code, "catastrophe": new_room.catastrophe,
                "bunker": new_room.bunker, "threat": new_room.threat
            }), 201)


@app.route('/bunker/api/v1/remove-room/<game_code>', methods=['POST'])
async def remove_room(game_code):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена."}), 404)
            await session.execute(
                delete(Room).where(Room.game_code == game_code)
            )
            await session.execute(
                delete(User).where(User.room_id == room_id)
            )
    return make_response(jsonify({"status": True}))


@app.route("/bunker/api/v1/game-code/<int:host_id>", methods=['GET'])
async def get_game_code_id(host_id):
    async with create_session() as session:
        async with session.begin():
            room = await session.execute(
                select(Room).where(Room.host_id == host_id)
            )
            room = room.scalars().first()
            if room is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена."}), 404)
            return make_response(jsonify({"game_code": room.game_code}), 200)


@app.route("/bunker/api/v1/reveal-characteristic/<game_code>/<int:user_id>", methods=["PATCH"])
async def reveal_characteristic(game_code, user_id):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена."}), 404)

            user = await session.execute(
                select(User).where(and_(User.room_id == room_id.id, User.user_id == user_id))
            )
            user = user.scalars().first()
            if user is None:
                return make_response(jsonify({"status": False, "error": "Пользователь не найден."}), 404)

            user.update(request.json["attribute"] + "_revealed")

            await session.commit()
    return make_response(jsonify({"status": True}), 201)


@app.route('/bunker/api/v1/leave-game/<game_code>/<int:user_id>', methods=['PATCH'])
async def leave_game(game_code, user_id):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена."}), 404)

            users = await session.execute(
                select(User).where(and_(User.room_id == room_id.id, User.user_id == user_id))
            )
            users = users.scalars().all()
            for i in users:
                i.leave()
            await session.commit()
    return make_response(jsonify({"status": True}), 201)


@app.route('/bunker/api/v1/use-active-card/<game_code>/<int:user_id>', methods=['POST'])
async def use_active_card(game_code, user_id):
    async with create_session() as session:
        async with session.begin():
            room = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room = room.scalars().first()
            room_id = room.id
            if room_id is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена."}), 404)

            user = await session.execute(select(User).where(
                and_(User.room_id == room_id, User.user_id == user_id)
            ))
            user = user.scalars().first()
            active_card = user.action_card
    try:
        async with httpx.AsyncClient() as client:
            active_card = await client.get(
                f"http://generator:4322/generator/api/v1/get-active-card/{active_card}"
            )
            active_card = active_card.json()
    except httpx.TimeoutException:
        return make_response(jsonify({"status": False, "error": "Превышено время ожидания запроса."}), 404)
    if not request.json["switch"] and active_card["id"] in [2, 6]:
        return make_response(jsonify({"status": False}), 424)
    async with create_session() as session:
        async with session.begin():
            if active_card["id"] == 3:
                player_card_attr = reg.findall(active_card["card"])[0]
                users = await session.execute(select(User).where(
                    and_(User.get_attr(player_card_attr, revealed=True), User.active, User.room_id == room_id)
                ))
                users = users.scalars().all()
                player = None
                for i in users:
                    if i.user_id == user_id:
                        player = i
                users = list(filter(lambda x: x.user_id != user_id, users))
                if not users or player is None:
                    return make_response({"status": False, "error": "Игрок не найден."}, 404)
                player_to_switch = random.choice(users)
                attr = player_to_switch.get_attr(player_card_attr)

                player_to_switch.set_attr(player_card_attr, player.get_attr(player_card_attr))
                player.set_attr(player_card_attr, attr)
                player_to_switch.switches += 1
                player.switches += 1
            elif active_card["id"] == 5:
                player_card_attr = reg.findall(active_card["card"])[0]
                users = await session.execute(select(User).where(
                    and_(User.get_attr(player_card_attr, revealed=True), User.active, User.room_id == room_id)
                ))
                users = users.scalars().all()
                attrs = [i.get_attr(player_card_attr) for i in users]
                random.shuffle(attrs)
                for i in range(len(users)):
                    users[i].set_attr(player_card_attr, attrs[i])
                    users[i].switches += 1
            elif active_card["id"] == 7:
                user.health = "Здоров 100%"
                user.switches += 1
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
                users = await session.execute(select(User).where(
                    and_(User.get_attr(player_card_attr, revealed=True), User.active, User.room_id == room_id)
                ))
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
                    return make_response({"status": False, "error": "Игрок не найден."}, 404)
                attr = player_to_switch.get_attr(player_card_attr)

                player_to_switch.set_attr(player_card_attr, player.get_attr(player_card_attr))
                player.set_attr(player_card_attr, attr)
                player_to_switch.switches += 1
                player.switches += 1
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
                    return make_response({"status": False, "error": "Игрок не найден."}, 404)
                
                player_to_switch.set_attr("Здоровье", "Здоров 100%")
                player_to_switch.switches += 1

            await session.commit()
            return make_response({"status": True}, 201)


@app.route("/bunker/api/v1/start-game/<game_code>", methods=['POST'])
async def start_game(game_code):
    async with create_session() as session:
        async with session.begin():
            room = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room = room.scalars().first()
            if room is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена"}), 404)
            room.started = True
            await session.commit()
            return make_response(jsonify({"status": True}), 201)


@app.route('/bunker/api/v1/add-user/<game_code>/<int:user_id>', methods=['POST'])
async def add_user(game_code, user_id):
    async with create_session() as session:
        async with session.begin():
            await session.execute(delete(User).where(User.user_id == user_id))
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена."}), 404)
            if room_id.started:
                return make_response(jsonify({"status": False, "error": "Игра уже идёт."}), 400)
            room_id = room_id.id
    try:
        async with httpx.AsyncClient() as client:
            user_data = await client.post(
                f"http://generator:4322/generator/api/v1/player/{game_code}", timeout=120
            )
            if user_data.status_code // 100 in [5, 4]:
                if 'application/json' in user_data.headers.get('Content-Type', ''):
                    return make_response(jsonify(
                        {"status": True, "error": user_data.json().get("error", None)}
                    ), user_data.status_code)
                return make_response({"status": False})
            user_data = user_data.json()
    except httpx.TimeoutException:
        return make_response(jsonify({"status": False, "error": "Превышено время ожидания запроса."}), 501)
    except (KeyError, json.decoder.JSONDecodeError):
        return make_response(jsonify({"status": False}), 501)
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
                return make_response(jsonify({"status": False}), 501)
            json_data["status"] = True
            return make_response(jsonify(json_data), 201)


@app.route("/bunker/api/v1/result/bunker", methods=["POST"])
async def bunker_result():
    async with httpx.AsyncClient() as client:
        try:
            result = await client.post(
                f"http://generator:4322/generator/api/v1/bunker-result",
                json=request.json,
                timeout=120
            )
        except httpx.TimeoutException:
            return make_response(jsonify({"status": False, "error": "Превышено время ожидания запроса."}), 501)
        if result.status_code // 100 in [5, 4]:
            if 'application/json' in result.headers.get('Content-Type', ''):
                return make_response(jsonify(
                    {"status": True, "error": result.json().get("error", None)}
                ), result.status_code)
            return make_response({"status": False}, 501)
        result = result.json()
    return make_response(jsonify(result), 201)


@app.route("/bunker/api/v1/user/add-vote/<game_code>/<int:user_id>", methods=["PUT"])
async def add_vote(game_code, user_id):

    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена"}), 404)

            user = await session.execute(
                select(User).where(and_(User.room_id == room_id.id, User.user_id == user_id))
            )
            user = user.scalars().first()
            if user is None:
                return make_response(jsonify({"status": False, "error": "Игрок не найден"}), 404)

            user.number_of_votes += 1

            return make_response(jsonify({"status": True}), 201)


@app.route("/bunker/api/v1/user/remove-vote/<game_code>/<int:user_id>", methods=["PUT"])
async def remove_vote(game_code, user_id):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена"}), 404)

            user = await session.execute(
                select(User).where(and_(User.room_id == room_id.id, User.user_id == user_id))
            )
            user = user.scalars().first()
            if user is None:
                return make_response(jsonify({"status": False, "error": "Игрок не найден."}), 404)

            user.number_of_votes -= 1

            return make_response(jsonify({"status": True}), 201)


@app.route("/bunker/api/v1/user/reset-vote/<game_code>", methods=["PUT"])
async def reset_vote(game_code):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена."}), 404)

            users = await session.execute(
                select(User).where(User.room_id == room_id.id)
            )
            users = users.scalars().all()
            if users is None:
                return make_response(jsonify({"status": False, "error": "Игроки не найдены."}), 404)

            for user in users:
                user.number_of_votes = 0

            return make_response(jsonify({"status": True}), 201)


@app.route("/bunker/api/v1/result/surface", methods=["POST"])
async def surface_result():
    async with httpx.AsyncClient() as client:
        try:
            result = await client.post(
                f"http://generator:4322/generator/api/v1/result",
                json=request.json,
                timeout=120
            )
        except httpx.TimeoutException:
            return make_response(jsonify({"status": False, "error": "Превышено время ожидания запроса."}), 501)
        if result.status_code // 100 in [5, 4]:
            if 'application/json' in result.headers.get('Content-Type', ''):
                return make_response(jsonify(
                    {"status": True, "error": result.json().get("error", None)}
                ), result.status_code)
            return make_response({"status": False}, 501)
        result = result.json()
    return make_response(jsonify(result), 201)


@app.route("/bunker/api/v1/get-game/<game_code>", methods=["GET"])
async def get_game(game_code):
    response = {}
    async with create_session() as session:
        async with session.begin():
            room = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room = room.scalars().first()
            if room is None:
                return make_response(jsonify({"status": False, "error": "Комната не найдена."}), 404)

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
                select(User).where(User.room_id == room.id)
            )
            users = users.scalars().all()

            for i in users:
                response["users"].append(
                    i.to_json()
                )

            return make_response(jsonify(response), 200)


@app.route("/bunker/api/v1/auth", methods=["POST", "GET"])
async def auth_user():
    if request.method == "GET":
        async with create_session() as session:
            async with session.begin():
                users = await session.execute(select(Auth).where(
                    and_(Auth.user_id.isnot(None))
                ))
                users = users.scalars().all()
                users = list(filter(lambda x: x.expiration(), users))
                return make_response(jsonify(list(map(lambda x: x.get_main_info(), users))), 200)

    token_hash = request.args.get("token_hash", None, str)
    user_id = request.args.get("user_id", None, int)
    expiration_date = request.args.get("expiration_date", None, str)
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
                return make_response(jsonify(response), 201)

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
                return make_response(jsonify(response), 404)
            message, code = auth.auth(user_id)
            return make_response(jsonify(message), code)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
