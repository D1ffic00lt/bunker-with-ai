# -*- coding: utf-8 -*-
import os
import warnings
import discord
import nest_asyncio
import logging

from asyncio import run

from bot import BunkerBOT
from config import PREFIX
from units.game import Game

warnings.filterwarnings("ignore")
nest_asyncio.apply()

logging.info("Program started")


async def main() -> None:
    intents = discord.Intents.all()
    intents.members = True
    intents.message_content = True

    BOT: BunkerBOT = BunkerBOT(
        command_prefix=PREFIX,
        intents=intents, case_insensitive=True
    )
    # logging.info("version: {}".format(__version__))

    await BOT.add_cog(Game(BOT))

    with open(os.environ.get('TOKEN')) as token_file:
        token = token_file.read()

    BOT.run(token)


if __name__ == '__main__':
    run(main())
