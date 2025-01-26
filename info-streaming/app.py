import base64
import io
import httpx

from copy import deepcopy
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketException, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from connector import Manager, WebSocketConnection, FrameStreamManager, get_not_found_frame

app = FastAPI()
frame_manager = FrameStreamManager()
api_manager = Manager(frame_manager)
templates = Jinja2Templates(directory="./templates")
not_found_frame: str | None = None


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


@app.get("/api/v1.1/user-frame/{host_id}/{user_id}", response_class=HTMLResponse)
async def get_user_frame(host_id: int, user_id: int, request: Request):
    return templates.TemplateResponse(
        name="ws_frame.html",
        context={
            "request": request,
            "host_id": str(host_id),
            "user_id": str(user_id)
        }
    )


@app.websocket("/api/v1/user-frame/{host_id}/{user_id}")
async def frame_stream(websocket: WebSocket, host_id: int, user_id: int):
    async with httpx.AsyncClient() as requests:
        game_code = await requests.get(f"http://api:9462/bunker/api/v1/game-code/{host_id}")
        if game_code.status_code // 100 in [4, 5]:
            await websocket.accept()
            await websocket.send_text(not_found_frame)
            return
        game_code = game_code.json()["game_code"]
        websocket = WebSocketConnection(websocket, game_code, user_id)
        await websocket.accept()

        frame_manager.active_connections[game_code].append(websocket)

        await websocket.send_text(not_found_frame)
        if not api_manager.exists(game_code):
            api_manager.create_connection(game_code)
            api_manager.wait_for_update(game_code)

        try:
            while True:
                await websocket.receive()
        except (WebSocketException, WebSocketDisconnect):
            await websocket.close()
