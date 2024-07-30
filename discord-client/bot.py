# -*- coding: utf-8 -*-
import logging
import random
import httpx
import discord

from discord.ext import commands

from units.auth import Auth
from config import PREFIX


class BunkerBOT(commands.Bot):
    ADMINISTRATORS = [401555829620211723]

    def __init__(self, command_prefix: str, *, intents: discord.Intents, **kwargs) -> None:
        super().__init__(command_prefix, intents=intents, **kwargs)
        self.remove_command('help')

        self.authenticated_users = []

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(f"{PREFIX}help")
        )
        async with httpx.AsyncClient() as requests:
            users = await requests.get("http://api:9462/bunker/api/v1/auth")
            users = users.json()
            self.authenticated_users = [Auth(i["user_id"], i["expiration_date"]) for i in users]
        logging.info(f"Bot connected")

    @commands.Cog.listener()
    async def on_command_error(
            self, ctx: commands.context.Context, error: Exception
    ) -> None:
        if isinstance(error, commands.CommandOnCooldown):
            pass
        elif isinstance(error, commands.CommandNotFound):
            pass
        logging.error(error)

    @staticmethod
    def generate_random_code() -> str:
        code_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        code = ''
        for i in range(0, 10):
            slice_start = random.randint(0, len(code_chars) - 1)
            code += code_chars[slice_start: slice_start + 1]
        return "/" + code
