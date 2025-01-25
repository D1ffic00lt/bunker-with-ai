from fastapi import WebSocket


class WebSocketConnection(object):
    def __init__(self, websocket: WebSocket, game_code: str):
        self.websocket = websocket
        self.game_code = game_code

    async def accept(self):
        return await self.websocket.accept()

    async def send_json(self, message: dict):
        return await self.websocket.send_json(message)

    async def receive_json(self):
        return await self.websocket.receive_json()

    async def close(self):
        return await self.websocket.close()

class WebSocketManager(object):
    def __init__(self):
        self.active_connections: dict[str, WebSocketConnection] = {}

    async def connect(self, websocket: WebSocketConnection, game_code: str):
        await websocket.accept()
        self.active_connections[game_code] = websocket
        print(f"Client connected to game {game_code}.")

    async def disconnect(self, websocket: WebSocketConnection, game_code: str):
        self.active_connections.pop(game_code)
        await websocket.close()
        print(f"Client disconnected from game {game_code}.")

    async def send_message(self, game_code: str, message: dict):
        if game_code in self.active_connections:
            try:
                await self.active_connections[game_code].send_json(message)
            except Exception as e:
                print(f"Error during sending message: {e}")
                await self.disconnect(self.active_connections[game_code], game_code)

    async def broadcast(self, message: dict):
        for connection in self.active_connections.values():
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error during sending message: {e}")
                await self.disconnect(connection, connection.game_code)

    async def remove_connection(self, game_code: str):
        if game_code in self.active_connections:
            await self.active_connections[game_code].close()
            self.active_connections.pop(game_code)
            print(f"Removed connection for game {game_code}.")
        else:
            print(f"Connection for game {game_code} not found.")