# -*- coding: utf-8 -*-
import logging
import random

import discord

from discord.ext import commands

from config import PREFIX


class BunkerBOT(commands.Bot):
    def __init__(self, command_prefix: str, *, intents: discord.Intents, **kwargs) -> None:
        super().__init__(command_prefix, intents=intents, **kwargs)
        self.remove_command('help')

    async def on_ready(self) -> None:
        await self.wait_until_ready()
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(f"{PREFIX}help")
        )
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