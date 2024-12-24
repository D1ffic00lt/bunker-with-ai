import base64
import io
import httpx

from copy import deepcopy
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="./templates")
not_found_frame = None
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
    "number_of_votes": 0,
    "active": True
}


async def get_not_found_frame():
    async with httpx.AsyncClient() as requests:
        try:
            raw_not_found_frame = await requests.post(
                "http://frame-generator:1334/api/v1/get-user-frame", json=not_found_frame_data
            )
        except httpx.TimeoutException:
            return b""
        if raw_not_found_frame.status_code // 100 in [4, 5]:
            return b""

        raw_not_found_frame = raw_not_found_frame.content
        raw_not_found_frame = base64.b64encode(io.BytesIO(raw_not_found_frame).getvalue()).decode('utf-8')

        return raw_not_found_frame


@app.on_event("startup")
async def setup_resources():
    global not_found_frame
    not_found_frame = await get_not_found_frame()


@app.get('/api/v1/url')
async def get_url():
    return JSONResponse({"url": "http://bunker.d1ffic00lt.com/"})


@app.get("/api/v1/bunker/{user_id}", response_class=HTMLResponse)
async def get_bunker(user_id: int, request: Request):
    async with httpx.AsyncClient() as requests:
        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{user_id}")
        if game_code.status_code // 100 in [4, 5]:
            raise HTTPException(status_code=game_code.status_code, detail="Error fetching game code")

        game_code = game_code.json()["game_code"]
        game = await requests.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code))
        if game.status_code // 100 in [4, 5]:
            raise HTTPException(status_code=game.status_code, detail="Error fetching game data")

        game = game.json()
        content = "Бункер" if not game["started"] else game["bunker"]
        return templates.TemplateResponse(
            name="index.html", context={"content": content, "request": request}
        )


@app.get("/api/v1/catastrophe/{user_id}", response_class=HTMLResponse)
async def get_catastrophe(user_id: int, request: Request):
    async with httpx.AsyncClient() as requests:
        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{user_id}")
        if game_code.status_code // 100 in [4, 5]:
            raise HTTPException(status_code=game_code.status_code, detail="Error fetching game code")

        game_code = game_code.json()["game_code"]
        game = await requests.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
        if game.status_code // 100 in [4, 5]:
            raise HTTPException(status_code=game.status_code, detail="Error fetching game data")

        game = game.json()
        content = "Катастрофа" if not game["started"] else game["catastrophe"]
        return templates.TemplateResponse(
            name="index.html", context={"content": content, "request": request}
        )


@app.get("/api/v1/threat-in-bunker/{user_id}", response_class=HTMLResponse)
async def get_threat(user_id: int, request: Request):
    async with httpx.AsyncClient() as requests:
        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{user_id}")
        if game_code.status_code // 100 in [4, 5]:
            raise HTTPException(status_code=game_code.status_code, detail="Error fetching game code")

        game_code = game_code.json()["game_code"]
        game = await requests.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
        if game.status_code // 100 in [4, 5]:
            raise HTTPException(status_code=game.status_code, detail="Error fetching game data")

        game = game.json()
        content = "Угроза в бункере" if not game["started"] else game["threat"]
        return templates.TemplateResponse(
            name="index.html", context={"content": content, "request": request}
        )


@app.get("/api/v1/user-frame/{host_id}/{user_id}", response_class=HTMLResponse)
async def get_user_frame(host_id: int, user_id: int, request: Request):
    async with httpx.AsyncClient() as requests:
        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{host_id}")
        if game_code.status_code // 100 in [4, 5]:
            return templates.TemplateResponse(
                name="frame.html", context={"image_base64": not_found_frame, "request": request}
            )

        game_code = game_code.json()["game_code"]
        game = await requests.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
        if game.status_code // 100 in [4, 5]:
            return templates.TemplateResponse(
                name="frame.html", context={"image_base64": not_found_frame, "request": request}
            )

        game = game.json()

        user_data = {}
        for user in game["users"]:
            if user["user_id"] == user_id:
                user_data = deepcopy(user)
                break

        if user_data == {}:
            return templates.TemplateResponse(
                name="frame.html", context={"image_base64": not_found_frame, "request": request}
            )
        frame = await requests.post("http://frame-generator:1334/api/v1/get-user-frame", json=user_data)
        if frame.status_code // 100 in [4, 5]:
            return templates.TemplateResponse(
                name="frame.html", context={"image_base64": not_found_frame, "request": request}
            )

        frame = frame.content
        frame = base64.b64encode(io.BytesIO(frame).getvalue()).decode('utf-8')
        return templates.TemplateResponse(
            name="frame.html", context={"image_base64": frame, "request": request}
        )
