import httpx

from flask import Flask, make_response, render_template

app = Flask(__name__)


@app.route("/api/v1/game/<int:user_id>", methods=["GET"])
async def get_game_info(user_id):
    async with httpx.AsyncClient() as requests:
        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{user_id}")
        game_code = game_code.json()["game_code"]
        game = await requests.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
        game = game.json()
    return make_response(render_template("index.html", content=game["bunker"]), 200)


if __name__ == "__main__":
    app.run(debug=False, port=5001)
