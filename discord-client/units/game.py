# -*- coding: utf-8 -*-
import asyncio
import functools

import discord
import httpx

from discord.ext import commands
from discord import app_commands
from typing import Any

from .button import ControlButtons
from .votes import StartVoteButton


class Game(commands.Cog):
    def __init__(self, bot: commands.Bot | Any, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.games = {}
        self.translate = {
            "action_card": "Карта действий 🎴",
            "age": "Возраст 👴",
            "fact1": "Факт 1 💌",
            "fact2": "Факт 2 💌",
            "gender": "Гендер 👴",
            "health": "Здоровье 💊",
            "hobby": "Хобби 💻",
            "luggage": "Багаж 🧳",
            "phobia": "Фобия 🤡",
            "profession": "Профессия 👩‍🚀"
        }
        self.sorting_indexes = [
            'user_id', 'room_id', 'gender', 'age', 'profession',
            'health', 'hobby', 'luggage', 'phobia', 'fact1',
            'fact2', 'action_card', 'active', 'gender_revealed',
            'health_revealed', 'profession_revealed',
            'hobby_revealed', 'luggage_revealed', 'action_card_revealed',
            'age_revealed', 'fact1_revealed', 'fact2_revealed',
            'phobia_revealed', 'number_of_votes', 'switches'
        ]

    async def check_auth(self, user_id, user_name, command):
        if user_id in self.bot.ADMINISTRATORS:
            print(f"PRIORITY LOGIN: {command} BY {user_name}")
            return True
        # print(self.bot.authenticated_users)
        for user in self.bot.authenticated_users:
            if user.user_id == user_id and user.check_expiration():
                print(f"LOGIN: {command} BY {user_name}")
                return True
        return False

    @app_commands.command(name="reset-votes", description="Обнуляет голосования")
    async def __reset_votes(self, inter: discord.Interaction, game_code: str):
        if not await self.check_auth(inter.user.id, inter.user.display_name, "reset-votes"):
            await inter.response.send_message("Вы не авторизированы!", ephemeral=True)
            return
        async with httpx.AsyncClient() as client:
            try:
                game = await client.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
                if game.status_code // 100 in [3, 4, 5]:
                    await inter.response.send_message("Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.response.send_message("Что-то пошло не так...")
                return
            game = game.json()
        if game["host_id"] != inter.user.id:
            await inter.response.send_message("Что-то пошло не так...")
            return  # TODO
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    "http://api:9462/bunker/api/v1/user/reset-vote/{}".format(game_code),
                    timeout=60
                )
                if response.status_code // 100 in [3, 4, 5]:
                    await inter.response.send_message("Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.response.send_message("Что-то пошло не так...")
                return
        await inter.response.send_message("Голосование перезагружено")
        message = await inter.original_response()
        await message.delete(delay=2)

    @app_commands.command(name="new-game", description="Создать новую игру")
    async def __new_game(self, inter: discord.Interaction) -> None:
        if not await self.check_auth(inter.user.id, inter.user.display_name, "new-game"):
            await inter.response.send_message("Вы не авторизированы!", ephemeral=True)
            return
        await inter.response.send_message("Создание...")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"http://api:9462/bunker/api/v1/new-game/{inter.user.id}", timeout=60
                )
                if response.status_code // 100 in [3, 4, 5]:
                    await inter.edit_original_response(content="Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.edit_original_response(content="Что-то пошло не так...")
                return
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
            try:
                url = await client.get(
                    "http://info-streaming:80/api/v1/url",
                    timeout=60
                )
                if url.status_code // 100 in [3, 4, 5]:
                    await inter.edit_original_response(content="Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.edit_original_response(content="Что-то пошло не так...")
                return
            url = url.json()["url"]

            await inter.edit_original_response(
                content=f"Игра создана! Код для входа: ||`{response['room']}`||\n\n"
                        f"Ссылка на информацию о катастрофе: ||{url + f'api/v1/catastrophe/{inter.user.id}'}||\n"
                        f"Ссылка на информацию о бункере: ||{url + f'api/v1/bunker/{inter.user.id}'}||\n"
                        f"Ссылка на угрозу в бункере: ||{url + f'api/v1/threat-in-bunker/{inter.user.id}'}||"
            )

    @app_commands.command(name="join", description="Присоединиться к игре")
    async def __join_game(self, inter: discord.Interaction, game_code: str) -> None:
        await inter.response.send_message("Вход в игру...")
        async with httpx.AsyncClient() as client:
            try:
                result = await client.post(
                    f"http://api:9462/bunker/api/v1/add-user/{game_code}/{inter.user.id}", timeout=60
                )
                if result.status_code // 100 in [3, 4, 5]:
                    await inter.edit_original_response(content="Что-то пошло не так...")
                    return
            except (httpx.TimeoutException, TypeError):
                await inter.edit_original_response(content="Что-то пошло не так...")
                return
            try:
                game = await client.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
                if game.status_code // 100 in [3, 4, 5]:
                    await inter.edit_original_response(content="Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.edit_original_response(content="Что-то пошло не так...")
                return
            try:
                url = await client.get(
                    "http://info-streaming:80/api/v1/url",
                    timeout=60
                )
                if url.status_code // 100 in [3, 4, 5]:
                    await inter.edit_original_response(content="Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.edit_original_response(content="Что-то пошло не так...")
                return
            url = url.json()["url"]
            host = game.json()["host_id"]
            host = await self.bot.fetch_user(host)
            await host.send(
                "<@{}> зашёл в игру. Ссылка на рамку: ||{}||".format(
                    inter.user.id, f"{url}api/v1/user-frame/{host.id}/{inter.user.id}"
                )
            )
            await inter.edit_original_response(
                content=f"Вы в игре!"
            )

    @app_commands.command(name="start", description="Начать игру")
    async def __start_game(self, inter: discord.Interaction, game_code: str) -> None:
        if not await self.check_auth(inter.user.id, inter.user.display_name, "start"):
            await inter.response.send_message("Вы не авторизированы!", ephemeral=True)
            return
        async with httpx.AsyncClient() as client:
            try:
                game = await client.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
                if game.status_code // 100 in [3, 4, 5]:
                    await inter.response.send_message("Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.response.send_message("Что-то пошло не так...")
                return
            game = game.json()
            if game["host_id"] != inter.user.id:
                await inter.response.send_message("Что-то пошло не так...")
                return  # TODO
            try:
                start = await client.post("http://api:9462/bunker/api/v1/start-game/{}".format(game_code), timeout=60)
                if start.status_code // 100 in [3, 4, 5]:
                    await inter.response.send_message("Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.response.send_message("Что-то пошло не так...")
                return
        game_description = discord.Embed(
            title="Сценарий",
            color=16711680
        )
        game_description.add_field(
            name='Катастрофа',
            value=game['catastrophe'][:1024],
            inline=False
        )
        game_description.add_field(
            name='Бункер',
            value=game['bunker'][:1024],
            inline=False
        )
        game_description.add_field(
            name='Угроза в бункере',
            value=game['threat'][:1024],
            inline=False
        )
        await inter.response.send_message("Игра началась!")
        for player in game["users"]:
            user = await self.bot.fetch_user(player["user_id"])
            user_desc = discord.Embed(
                title="Ваши характеристики",
                description="Вы можете вскрыть свою характеристику нажатием на кнопки ниже, "
                            "но помните, что **вскрытые характеристики не получится снова скрыть!**",
                color=1835263
            )
            user_desc.set_author(name=user.display_name)
            user_desc.set_thumbnail(url=user.avatar.url)
            user_desc.set_footer(
                text="В случае неисправностей вы можете попросить хоста прописать команду /start снова "
                     "или обратиться к администратору (D1ffic00lt)",
                icon_url="https://avatars.githubusercontent.com/u/69642892?v=4"
            )
            for h in sorted(player, key=lambda x: self.sorting_indexes.index(x)):
                if h in [
                    "active", "user_id", "room_id", "number_of_votes", "switches"
                ] or "revealed" in h:
                    continue
                try:
                    user_desc.add_field(
                        name=self.translate[h],
                        value=player[h][0].upper() + player[h][1:]
                    )
                except KeyError:
                    pass
            view = ControlButtons(game_code, bot=self.bot, user_data=player)
            if player["user_id"] == game["host_id"]:
                view.add_item(StartVoteButton(label="Начать голосование"))
            await user.send(embeds=[game_description, user_desc], view=view)
            await asyncio.sleep(0.5)

    @app_commands.command(name="get-result", description="Получить итоги игры")
    async def __get_result(self, inter: discord.Interaction, game_code: str) -> None:
        if not await self.check_auth(inter.user.id, inter.user.display_name, "get-result"):
            await inter.response.send_message("Вы не авторизированы!", ephemeral=True)
            return
        await inter.response.send_message("Отправляю результаты. Это может занять какое-то время.")
        async with httpx.AsyncClient() as client:
            try:
                game = await client.get(
                    "http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60
                )
                if game.status_code // 100 in [3, 4, 5]:
                    await inter.edit_original_response(content="Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.edit_original_response(content="Что-то пошло не так...")
                return
            game = game.json()
            if game["host_id"] != inter.user.id:
                return  # TODO
            try:
                bunker_result = await client.post(
                    "http://api:9462/bunker/api/v1/result/bunker", json=game, timeout=60
                )
                if bunker_result.status_code // 100 in [3, 4, 5]:
                    await inter.edit_original_response(content="Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.edit_original_response(content="Что-то пошло не так...")
                return
            try:
                surface_result = await client.post(
                    "http://api:9462/bunker/api/v1/result/surface", json=game, timeout=60
                )
                if surface_result.status_code // 100 in [3, 4, 5]:
                    await inter.edit_original_response(content="Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.edit_original_response(content="Что-то пошло не так...")
                return
            bunker_result = bunker_result.json()
            surface_result = surface_result.json()
        try:
            bunker_result_emb = discord.Embed(
                title="Судьба людей в бункере",
                description=bunker_result['result']
            )
            bunker_result_emb.set_footer(
                text="Вы можете сгенерировать результаты снова, если считаете их неудовлетворительными.",
                icon_url="https://avatars.githubusercontent.com/u/69642892?v=4"
            )
            surface_result_emb = discord.Embed(
                title="Судьба людей вне бункера",
                description=surface_result['result']
            )
            surface_result_emb.set_footer(
                text="Вы можете сгенерировать результаты снова, если считаете их неудовлетворительными.",
                icon_url="https://avatars.githubusercontent.com/u/69642892?v=4"
            )
        except TypeError:
            await inter.response.send_message("что-то пошло не так...")
            return
        for player in game["users"]:
            user = await self.bot.fetch_user(player["user_id"])
            await user.send(embeds=[bunker_result_emb, surface_result_emb])
            await asyncio.sleep(0.5)
        await inter.edit_original_response(
            content=f"Отправлено."
        )

    @app_commands.command(name="get-frame", description="Получить рамку")
    async def __get_frame(self, inter: discord.Interaction, member: discord.Member) -> None:
        await inter.response.send_message(
            f"Рамка {member.mention}: ||http://127.0.0.1:5001/api/v1/user-frame/{inter.user.id}/{member.id}||",
            ephemeral=True
        )

    @app_commands.command(name="leave", description="Покинуть игру")
    async def __leave(self, inter: discord.Interaction, game_code: str) -> None:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    "http://api:9462/bunker/api/v1/leave-game/{}/{}".format(game_code, inter.user.id)
                )
                if response.status_code // 100 in [3, 4, 5]:
                    await inter.edit_original_response(content="Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.response.send_message(content="Что-то пошло не так...")
                return
        await inter.response.send_message("Успешно!")

    @staticmethod
    async def get_id(game_code):
        async with httpx.AsyncClient() as client:
            try:
                game = await client.get("http://api:9462/bunker/api/v1/get-game/{}".format(game_code), timeout=60)
                if game.status_code // 100 in [3, 4, 5]:
                    return -1
            except httpx.TimeoutException:
                return -1
            game = game.json()
        return game["host_id"]

    @commands.command()
    async def sync(self, ctx: commands.context.Context, type_: str = "local"):
        if ctx.author.id in self.bot.ADMINISTRATORS:
            if type_ == "global":
                fmt = await ctx.bot.tree.sync()
                await ctx.reply(f"Synced {len(fmt)} (global)")
            else:
                fmt = await ctx.bot.tree.sync(guild=ctx.guild)
                await ctx.reply(f"Synced {len(fmt)}")
        else:
            await ctx.message.add_reaction('❌')
