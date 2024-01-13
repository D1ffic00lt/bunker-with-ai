# -*- coding: utf-8 -*-
import logging
import discord
import httpx

from discord.ext import commands
from discord import app_commands


class Game(commands.Cog):
    def __init__(self, bot: commands.Bot, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.games = {}
        self.translate = {
            "action_card": "Карта действий",
            "age": "Возраст",
            "fact1": "Факт 1",
            "fact2": "Факт 2",
            "gender": "Гендер",
            "health": "Здоровье",
            "hobby": "Хобби",
            "luggage": "Багаж",
            "phobia": "Фобия",
            "profession": "Профессия"
        }
        logging.info(f"Game (Slash) connected")

    @app_commands.command(name="new-game")
    async def __new_game(self, inter: discord.Interaction) -> None:
        if not self.check_role_exists(inter.user.id):
            return
        await inter.response.send_message("Создание...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://api:9462/bunker/api/v1/new-game/{inter.user.id}", timeout=60
            )
            if response.status_code == 201:
                response = response.json()
            # print(response)
            self.games[inter.user.id] = {
                "game_code": response["room"],
                "catastrophe": response["catastrophe"],
                "bunker": response["bunker"],
                "threat": response["threat"],
                "users": {}
            }
            await inter.edit_original_response(
                content=f"Игра создана! Код для входа: ||`{response['room']}`||"
            )

    @app_commands.command(name="join")
    async def __join_game(self, inter: discord.Interaction, game_code: str) -> None:
        if not self.check_role_exists(inter.user.id):
            return
        await inter.response.send_message("Вход в игру...")
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"http://api:9462/bunker/api/v1/add-user/{game_code}/{inter.user.id}", timeout=60
                )
            except TypeError:
                await inter.edit_original_response(
                    content=f"Что-то пошло не так!"
                )
                return
            await inter.edit_original_response(
                content=f"Вы в игре!"
            )

    @app_commands.command(name="start")
    async def __start_game(self, inter: discord.Interaction, game_code: str) -> None:
        if not self.check_role_exists(inter.user.id):
            return
        async with httpx.AsyncClient() as client:
            game = await client.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
            game = game.json()
        if game["host_id"] != inter.user.id:
            return  # TODO
        game_gesc = (f"**Сценарий**:\n```\n{game['catastrophe']}\n```\n"
                     f"**Бункер**:\n```\n{game['bunker']}\n```\n"
                     f"**Угроза**:\n```\n{game['threat']}\n```")
        await inter.response.send_message("Игра началась!")
        for player in game["users"]:
            user = await self.bot.fetch_user(player["user_id"])
            user_desc = """ты:\n```\n"""
            for h in player:
                if h in ["active", "user_id"]:
                    continue
                try:
                    user_desc += "{}: {}\n".format(self.translate[h], player[h][0].upper() + player[h][1:])
                except KeyError:
                    pass
            user_desc += "```"
            await user.send(game_gesc)
            await user.send(user_desc)

    @app_commands.command(name="get-result")
    async def __gat_result(self, inter: discord.Interaction, game_code: str) -> None:
        if not self.check_role_exists(inter.user.id):
            return
        await inter.response.send_message("Отправляю результаты. Это может занять какое-то время.")
        async with httpx.AsyncClient() as client:
            game = await client.get(
                "http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60
            )
            game = game.json()
            bunker_result = await client.post(
                "http://api:9462/bunker/api/v1/result/bunker/", json=game, timeout=60
            )
            surface_result = await client.post(
                "http://api:9462/bunker/api/v1/result/surface/", json=game, timeout=60
            )
            bunker_result = bunker_result.json()
            surface_result = surface_result.json()
        try:
            bunker_result = f"Судьба людей в бункере: \n```\n{bunker_result['result']}\n```\n"
            surface_result = f"Судьба людей вне бункере: \n```\n{surface_result['result']}\n```\n"
        except TypeError:
            await inter.response.send_message("что-то пошло не так...")
        for player in game["users"]:
            user = await self.bot.fetch_user(player["user_id"])

            await user.send(bunker_result)
            await user.send(surface_result)
        await inter.edit_original_response(
            content=f"Отправлено."
        )

    @app_commands.command(name="leave")
    async def __leave(self, inter: discord.Interaction, game_code: str) -> None:
        if not self.check_role_exists(inter.user.id):
            return
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://api:9462/bunker/api/v1/leave-game/{}/{}".format(game_code, inter.user.id), timeout=60
            )
        await inter.response.send_message("Успешно!")

    @staticmethod
    async def get_id(game_code):
        async with httpx.AsyncClient() as client:
            game = await client.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
            game = game.json()
        return game["host_id"]

    def check_role_exists(self, user_id):
        # if host:
        #     return user_id == 248021970774392832
        if user_id == 401555829620211723:
            return True
        guild = self.bot.get_guild(902508714383261696)
        member = guild.get_member(user_id)
        for i in member.roles:
            if i.id == 1229399905647460392:
                return True
        return False

    @commands.command()
    async def sync(self, ctx: commands.context.Context, type_: str = "local"):
        if ctx.author.id == 401555829620211723:
            if type_ == "global":
                fmt = await ctx.bot.tree.sync()
                await ctx.reply(f"Synced {len(fmt)} (global)")
            else:
                fmt = await ctx.bot.tree.sync(guild=ctx.guild)
                await ctx.reply(f"Synced {len(fmt)}")
        else:
            await ctx.message.add_reaction('❌')
