import base64
import io
import types
import httpx
import redis

from copy import deepcopy
from flask import Flask, make_response, render_template, jsonify

app = Flask(__name__)
redis_db = redis.Redis(host='redis', port=1239, db=0, decode_responses=True)
not_found_frame_data = {
    "gender_revealed": False,
    "age_revealed": False,
    "profession_revealed": False,
    "health_revealed": False,
    "luggage_revealed": False,
    "fact1_revealed": False,
    "fact2_revealed": False,
    "phobia_revealed": False,
    "hobby_revealed": False,
    "number_of_votes": 0
}


@app.route('/api/v1/url', methods=['GET'])
async def get_url():
    return make_response(jsonify({"url": "http://127.0.0.1:5001/"}), 200)  # TODO


@app.route("/api/v1/bunker/<int:user_id>", methods=["GET"])
async def get_bunker(user_id):
    async with httpx.AsyncClient() as requests:
        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{user_id}")
        if game_code.status_code // 100 in [4, 5]:
            return make_response(jsonify({"status": False}), game_code.status_code)

        game_code = game_code.json()["game_code"]
        game = await requests.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code))
        if game.status_code // 100 in [4, 5]:
            return make_response(jsonify({"status": False}), game.status_code)

        game = game.json()
        if not game["started"]:
            return make_response(render_template("index.html", content="Бункер"), 200)
    return make_response(render_template("index.html", content=game["bunker"]), 200)


@app.route("/api/v1/catastrophe/<int:user_id>", methods=["GET"])
async def get_catastrophe(user_id):
    async with httpx.AsyncClient() as requests:
        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{user_id}")
        if game_code.status_code // 100 in [4, 5]:
            return make_response(jsonify({"status": False}), game_code.status_code)

        game_code = game_code.json()["game_code"]
        game = await requests.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
        if game.status_code // 100 in [4, 5]:
            return make_response(jsonify({"status": False}), game.status_code)

        game = game.json()
        if not game["started"]:
            return make_response(render_template("index.html", content="Катастрофа"), 200)
    return make_response(render_template("index.html", content=game["catastrophe"]), 200)


@app.route("/api/v1/threat-in-bunker/<int:user_id>", methods=["GET"])
async def get_threat(user_id):
    async with httpx.AsyncClient() as requests:
        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{user_id}")
        if game_code.status_code // 100 in [4, 5]:
            return make_response(jsonify({"status": False}), game_code.status_code)

        game_code = game_code.json()["game_code"]
        game = await requests.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
        if game.status_code // 100 in [4, 5]:
            return make_response(jsonify({"status": False}), game.status_code)

        game = game.json()
        if not game["started"]:
            return make_response(render_template("index.html", content="Угроза в бункере"), 200)
    return make_response(render_template("index.html", content=game["threat"]), 200)


@app.route("/api/v1/user-frame/<int:host_id>/<int:user_id>")
async def get_user_frame(host_id, user_id):
    async with httpx.AsyncClient() as requests:
        async def get_not_found_frame():
            if redis_db.exists(f"frame_not_found"):
                not_found_frame = redis_db.get(f"frame_not_found")
                return not_found_frame
            try:
                not_found_frame = await requests.post(
                    "http://frame-generator:1334/api/v1/get-user-frame", json=not_found_frame_data
                )
            except httpx.TimeoutException:
                return make_response(jsonify({"status": False}), 501)
            if not_found_frame.status_code // 100 in [4, 5]:
                return make_response(jsonify({"status": False}), not_found_frame.status_code)

            not_found_frame = not_found_frame.content
            not_found_frame = base64.b64encode(io.BytesIO(not_found_frame).getvalue()).decode('utf-8')
            awaitable_frame = redis_db.set(f"frame_not_found", not_found_frame)

            if isinstance(awaitable_frame, types.CoroutineType):
                print("some problem...")

            return not_found_frame

        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{host_id}")
        if game_code.status_code // 100 in [4, 5]:
            return render_template("frame.html", image_base64=(await get_not_found_frame()))

        game_code = game_code.json()["game_code"]
        game = await requests.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
        if game.status_code // 100 in [4, 5]:
            return render_template("frame.html", image_base64=(await get_not_found_frame()))

        game = game.json()

        user_data = {}
        for user in game["users"]:
            if user["user_id"] == user_id:
                user_data = deepcopy(user)
                break

        if user_data == {}:
            return make_response(jsonify({"status": False}), 404)
        user_code = (f"{user_data['gender_revealed']}{user_data['health_revealed']}{user_data['profession_revealed']}"
                     f"{user_data['hobby_revealed']}{user_data['luggage_revealed']}{user_data['age_revealed']}"
                     f"{user_data['fact1_revealed']}{user_data['fact2_revealed']}{user_data['phobia_revealed']}"
                     f"{user_data['number_of_votes']}")

        if redis_db.get(f"{host_id}:{user_id}") == user_code and redis_db.exists(f"frame_{host_id}:{user_id}"):
            frame = redis_db.get(f"frame_{host_id}:{user_id}")
            return render_template("frame.html", image_base64=frame)
        awaitable = redis_db.set(f"{host_id}:{user_id}", user_code)

        if isinstance(awaitable, types.CoroutineType):
            print("some problem...")

        frame = await requests.post("http://frame-generator:1334/api/v1/get-user-frame", json=user_data)
        if frame.status_code // 100 in [4, 5]:
            return render_template("frame.html", image_base64=await get_not_found_frame())

        frame = frame.content
        frame = base64.b64encode(io.BytesIO(frame).getvalue()).decode('utf-8')
        awaitable = redis_db.set(f"frame_{host_id}:{user_id}", frame)

        if isinstance(awaitable, types.CoroutineType):
            print("some problem...")

        return render_template("frame.html", image_base64=frame)


if __name__ == "__main__":
    app.run(debug=False, port=5001)
