# -*- coding: utf-8 -*-
import os
import warnings
import discord
import nest_asyncio
import logging

from asyncio import run

from bot import BunkerBOT
from units.game import Game
from units.info import Info
from units.auth import UserAuth

warnings.filterwarnings("ignore")
nest_asyncio.apply()

logging.info("Program started")

async def main() -> None:
    intents = discord.Intents.all()
    intents.members = True
    intents.message_content = True

    if os.environ.get("PROXY"):
        print(f"USING PROXY: {os.environ.get('PROXY')}")

    bot: BunkerBOT = BunkerBOT(
        command_prefix=os.environ.get("PREFIX", "/"),
        intents=intents, case_insensitive=True,
        proxy=os.environ.get("PROXY", None),
    )
    # logging.info("version: {}".format(__version__))

    await bot.add_cog(Game(bot))
    await bot.add_cog(Info(bot))
    await bot.add_cog(UserAuth(bot))

    with open(os.environ.get('TOKEN')) as token_file:
        token = token_file.read()

    bot.run(token)


if __name__ == '__main__':
    run(main())
