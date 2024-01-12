import asyncio
import json
import os.path
import random
import httpx

from flask import Flask, make_response, jsonify, request
from sqlalchemy import select, delete

from database.db_session import create_session, global_init
from database.rooms import Room
from database.users import User

app = Flask(__name__)

if not os.path.isdir(".database/"):
    os.mkdir(".database/")
asyncio.run(global_init("./.database/games.db"))


def get_promo_code(num_chars) -> str:
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
            await session.execute(delete(Room).where(Room.host_id == user_id))
            try:
                async with httpx.AsyncClient() as client:
                    cat = await client.post("http://generator:4322/generator/api/v1/catastrophe", timeout=60)
                    cat = cat.json()
                    bunker = await client.post("http://generator:4322/generator/api/v1/bunker", timeout=60)
                    bunker = bunker.json()

                new_room = Room()
                new_room.host_id = user_id
                new_room.bunker = bunker["desc"]
                new_room.threat = bunker["threat"]
                new_room.catastrophe = cat["desc"]
                new_room.game_code = get_promo_code(32)
                session.add(new_room)
                return make_response(jsonify({
                    "room": new_room.game_code, "catastrophe": new_room.catastrophe,
                    "bunker": new_room.bunker, "threat": new_room.threat
                }), 201)
            except (KeyError, json.decoder.JSONDecodeError):  # FIXME
                return make_response(jsonify({"status": False}), 501)


@app.route('/bunker/api/v1/remove-room/<game_code>', methods=['POST'])
async def remove_room(game_code):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return
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
                return make_response(jsonify({"status": False}), 404)
            return make_response(jsonify({"game_code": room.game_code}), 200)


@app.route('/bunker/api/v1/leave-game/<game_code>/<int:user_id>', methods=['POST'])
async def leave_game(game_code, user_id):
    async with create_session() as session:
        async with session.begin():
            room_id = await session.execute(
                select(Room).where(Room.game_code == game_code)
            )
            room_id = room_id.scalars().first()
            if room_id is None:
                return make_response(jsonify({"status": False}), 404)

            user = await session.execute(
                select(User).where(User.room_id == room_id.id and User.user_id == user_id)
            )
            user = user.scalars().first()
            if user is None:
                return make_response(jsonify({"status": False}), 404)

            user.active = False
            await session.commit()
            return make_response(jsonify({"status": True}), 201)


@app.route('/bunker/api/v1/add-user/<game_code>/<int:user_id>', methods=['POST'])
async def add_user(game_code, user_id):
    async with create_session() as session:
        async with session.begin():
            try:
                room_id = await session.execute(
                    select(Room).where(Room.game_code == game_code)
                )
                room_id = room_id.scalars().first()
                if room_id is None:
                    return make_response(jsonify({"status": False}), 404)
                room_id = room_id.id
                async with httpx.AsyncClient() as client:
                    user_data = await client.post(f"http://generator:4322/generator/api/v1/player/{game_code}", timeout=60)
                    user_data = user_data.json()
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
                json_data = user.to_json()
                json_data["status"] = True
                return make_response(jsonify(json_data), 201)
            except (KeyError, json.decoder.JSONDecodeError):
                # raise e
                return make_response(jsonify({"status": False}), 501)


@app.route("/bunker/api/v1/result/bunker/", methods=["POST"])
async def bunker_result():
    async with httpx.AsyncClient() as client:
        result = await client.post(f"http://generator:4322/generator/api/v1/bunker-result", json=request.json, timeout=60)
        result = result.json()
    return make_response(jsonify(result), 201)


@app.route("/bunker/api/v1/result/surface/", methods=["POST"])
async def surface_result():
    async with httpx.AsyncClient() as client:
        result = await client.post(f"http://generator:4322/generator/api/v1/result", json=request.json, timeout=60)
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

            response["id"] = room.id
            response["host_id"] = room.host_id
            response["game_code"] = room.game_code
            response["bunker"] = room.bunker
            response["threat"] = room.threat
            response["catastrophe"] = room.catastrophe
            response["users"] = []
            users = await session.execute(
                select(User).where(User.room_id == room.id)
            )
            users = users.scalars().all()

            for i in users:
                response["users"].append(
                    {
                        "user_id": i.user_id,
                        "gender": i.gender,
                        "health": i.health,
                        "profession": i.profession,
                        "hobby": i.hobby,
                        "luggage": i.luggage,
                        "action_card": i.action_card,
                        "phobia": i.phobia,
                        "age": i.age,
                        "fact1": i.fact1,
                        "fact2": i.fact2,
                        "active": i.active
                    }
                )
            # print(response)
            return make_response(jsonify(response), 200)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
