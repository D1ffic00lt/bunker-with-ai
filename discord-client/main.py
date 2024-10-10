# -*- coding: utf-8 -*-
import os
import warnings
import discord
import nest_asyncio

from bot import BunkerBOT
from units.game import Game
from units.info import Info
from units.auth import UserAuth

nest_asyncio.apply()

async def main() -> None:
    if os.environ.get("PROXY"):
        proxy = os.environ.get("PROXY")
        if "http" not in proxy:
            if not os.path.exists(proxy):
                warnings.warn("\033[93mPROXY FORMAT IS WRONG!!! IT MUST BE PATH-LIKE OR URL-LIKE!!!\033[0m")
                proxy = None
            else:
                with open(proxy, "r") as proxy_file:
                    proxy = proxy_file.read().strip()
                if "http" not in proxy:
                    warnings.warn("\033[93mPROXY FORMAT IS WRONG!!! IT MUST BE URL!!!\033[0m")
                    proxy = None
        if proxy:
            print(f"USING PROXY: {proxy}")

    warnings.filterwarnings("ignore")

    intents = discord.Intents.all()
    intents.members = True
    intents.message_content = True

    bot: BunkerBOT = BunkerBOT(
        command_prefix=os.environ.get("PREFIX", "/"),
        intents=intents, case_insensitive=True,
        proxy=proxy,
    )
    # logging.info("version: {}".format(__version__))

    await bot.add_cog(Game(bot))
    await bot.add_cog(Info(bot))
    await bot.add_cog(UserAuth(bot))

    with open(os.environ.get('TOKEN')) as token_file:
        token = token_file.read()

    bot.run(token)


if __name__ == '__main__':
    import asyncio

    asyncio.run(main())
