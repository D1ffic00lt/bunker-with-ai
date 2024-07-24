import asyncio
import discord
import httpx

from discord import Interaction


class StartVoteButton(discord.ui.Button):
    async def callback(self, inter: discord.Interaction):

        await inter.response.defer()
        async with httpx.AsyncClient() as client:
            try:
                game = await client.get(
                    "http://api:9462/bunker/api/v1/get-game/{}".format(self.view.game_code),
                    timeout=60
                )
                if game.status_code // 100 in [4, 5]:
                    await inter.response.send_message("Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.response.send_message("Что-то пошло не так...")
                return
            game = game.json()
        messages = []
        users = []
        for i in game["users"]:
            user: discord.User = await self.view.bot.fetch_user(i["user_id"])
            users.append((user, i["active"]))
            await asyncio.sleep(0.2)
        # FIXME: PLS
        host_active = False
        for player in game["users"]:
            if player["user_id"] == game["host_id"]:
                host_active = player["active"]
            view = VoteControlButtons(self.view.game_code, self.view.bot)
            for p in users:
                button = VoteButton(
                    label=p[0].name,
                    custom_id=str(p[0].id) + self.view.bot.generate_random_code(),
                    emoji="🪦"
                )
                if not p[1]:
                    button.disabled = True
                    button.custom_id = "-1" + self.view.bot.generate_random_code()
                view.add_item(button)
            if not player["active"] or player["user_id"] == game["host_id"]:
                continue
            user: discord.User = await self.view.bot.fetch_user(player["user_id"])
            message = await user.send("Голосование!", view=view)
            await asyncio.sleep(0.5)
            messages.append(message)
        view = VoteControlButtons(self.view.game_code, self.view.bot)
        for p in game["users"]:
            user: discord.User = await self.view.bot.fetch_user(p["user_id"])
            button = VoteButton(
                label=user.name, custom_id=str(user.id) + self.view.bot.generate_random_code(), emoji="🪦"
            )
            if not p["active"] or not host_active:
                button.disabled = True
                button.custom_id = "-1" + self.view.bot.generate_random_code()
            view.add_item(button)
            await asyncio.sleep(0.2)
        button = VoteButton(
            label="Закончить голосование", custom_id="stop_vote" + self.view.bot.generate_random_code()
        )
        view.add_item(button)
        message = await inter.followup.send("Голосование", view=view)
        messages.append(message)
        view.messages = messages


class VoteButton(discord.ui.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clicked = False

    async def callback(self, inter: Interaction):
        if self.custom_id.split("/")[0] == "-1":
            self.disabled = True
            return
        if self.custom_id.split("/")[0] == "stop_vote":
            for i in self.view.messages:
                try:
                    if isinstance(i, discord.Message):
                        await i.delete()
                    elif isinstance(i, discord.Interaction):
                        await i.delete_original_response()
                except discord.errors.HTTPException:
                    pass
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.put(
                        "http://api:9462/bunker/api/v1/user/reset-vote/{}".format(self.view.game_code),
                        timeout=60
                    )
                    if response.status_code // 100 in [4, 5]:
                        await inter.response.send_message("Что-то пошло не так...")
                        return
                except httpx.TimeoutException:
                    await inter.response.send_message("Что-то пошло не так...")
                    return
        else:
            for i in self.view.children:
                if i.custom_id.split("/")[0] == "stop_vote" or i.custom_id.split("/")[0] == "-1":
                    continue
                if i.clicked:
                    async with httpx.AsyncClient() as client:
                        try:
                            await client.put(
                                "http://api:9462/bunker/api/v1/user/remove-vote/{}/{}".format(
                                    self.view.game_code, i.custom_id.split("/")[0]
                                ),
                                timeout=60
                            )
                        except httpx.TimeoutException:
                            pass
                    i.clicked = False
                    i.disabled = False
            self.clicked = True
            self.disabled = True
            async with httpx.AsyncClient() as client:
                try:
                    await client.put(
                        "http://api:9462/bunker/api/v1/user/add-vote/{}/{}".format(
                            self.view.game_code, self.custom_id.split("/")[0]
                        ),
                        timeout=60
                    )
                except httpx.TimeoutException:
                    pass
            await inter.message.edit(view=self.view)
            await inter.response.send_message("Голос засчитан")
            message = await inter.original_response()
            await message.delete(delay=2)


class VoteControlButtons(discord.ui.View):
    def __init__(self, code, bot):
        super().__init__(timeout=None)
        self.messages = []
        self.game_code = code
        self.bot = bot
