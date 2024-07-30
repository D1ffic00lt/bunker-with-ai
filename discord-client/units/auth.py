import hashlib
import discord
import httpx

from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from typing import Any


class UserAuth(commands.Cog):
    def __init__(self, bot: commands.Bot | Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot

    @app_commands.command(name="auth", description="Авторизация для создания игр")
    async def __auth(self, inter: discord.Interaction, token: str):
        token = token.strip()
        for user in self.bot.authenticated_users:
            if user.user_id == inter.user.id and user.expiration:
                await inter.response.send_message("Вы уже авторизованы!", ephemeral=True)
                return
        async with httpx.AsyncClient() as client:
            result = await client.post(
                "http://api:9462/bunker/api/v1/auth",
                params={
                    "user_id": inter.user.id,
                    "token_hash": Auth.hash_token(token)
                }
            )
            if result.status_code == 400:
                await inter.response.send_message("ID токена не совпадает с вашим!", ephemeral=True)
                return
            if result.status_code == 404:
                await inter.response.send_message("Токен не найден!", ephemeral=True)
                return
            if result.status_code == 401:
                await inter.response.send_message("Срок действия токена истек!", ephemeral=True)
                return
            auth = Auth(inter.user.id, result.json()["expiration_date"])
            self.bot.authenticated_users.append(auth)
            await inter.response.send_message("Успешно!", ephemeral=True)

    @app_commands.command(name="create-token", description="Создать токен для авторизации")
    @app_commands.choices(
        unit=[
            app_commands.Choice(name="Секунд", value=1),
            app_commands.Choice(name="Минут", value=60),
            app_commands.Choice(name="Часов", value=3600),
            app_commands.Choice(name="Дней", value=86400)
        ]
    )
    async def __create_token(
            self, inter: discord.Interaction, duration: int = 1,
            unit: app_commands.Choice[int] = None
    ):
        if inter.user.id not in self.bot.ADMINISTRATORS:
            await inter.response.send_message("У вас недостаточно прав!", ephemeral=True)
            return
        if unit is None:
            duration = 86400
        else:
            duration = duration * unit.value
        async with httpx.AsyncClient() as client:
            result = await client.post(
                "http://api:9462/bunker/api/v1/auth",
                params={
                    "expiration_date": (datetime.now() + timedelta(seconds=duration)).strftime("%x %X")
                }
            )
            if result.status_code != 201:
                await inter.response.send_message("Что-то пошло не так...", ephemeral=True)
                return
            await inter.response.send_message(f"Токен: ||{result.json()['token']}||", ephemeral=True)


class Auth(object):
    def __init__(
            self, user_id: int, expiration_date: str
    ):
        self.user_id = user_id
        self.expiration_date = datetime.strptime(expiration_date, "%x %X")

    @staticmethod
    def hash_token(password: str):
        return hashlib.sha256(password.encode()).hexdigest()

    def check_expiration(self):
        return datetime.now() < self.expiration_date

    def __str__(self):
        return f"Auth({self.user_id}, {self.expiration_date})"

    def __repr__(self):
        return f"Auth({self.user_id}, {self.expiration_date})"
