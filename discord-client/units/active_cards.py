import random
import discord
import httpx

from discord import Interaction


class ActiveCardPlayer(discord.ui.Button):
    @staticmethod
    def generate_random_code() -> str:
        code_chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
        code = ''
        for i in range(0, 10):
            slice_start = random.randint(0, len(code_chars) - 1)
            code += code_chars[slice_start: slice_start + 1]
        return "/" + code

    async def callback(self, inter: discord.Interaction):

        await inter.response.defer()
        async with httpx.AsyncClient() as client:
            try:
                game = await client.get(
                    "http://api:9462/bunker/api/v1/get-game/{}".format(self.view.game_code),
                    timeout=60
                )
                if game.status_code // 100 in [4, 5]:
                    await inter.followup.send("Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.followup.send("Что-то пошло не так...")
                return
            game = game.json()
        view = ActiveCardControlButtons(self.view.game_code, self.view.bot)
        for p in game["users"]:
            user: discord.User = await self.view.bot.fetch_user(p["user_id"])
            button = ActiveCardButton(label=user.name, custom_id=str(user.id) + self.generate_random_code(), emoji="🪦")
            if not p["active"] or p["user_id"] != inter.user.id:
                button.disabled = True
                button.custom_id = "-1" + self.generate_random_code()
            view.add_item(button)
        button = ActiveCardButton(label="Отмена", custom_id="stop_vote" + self.generate_random_code())
        view.add_item(button)
        message = await inter.followup.send("Выберите игрока", view=view)
        view.messages = [message]


class ActiveCardButton(discord.ui.Button):
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
        else:
            ...
            await inter.message.edit(view=self.view)
            await inter.response.send_message("Использовано")
            message = await inter.original_response()
            await message.delete(delay=2)


class ActiveCardControlButtons(discord.ui.View):
    def __init__(self, code, bot):
        super().__init__(timeout=None)
        self.messages = []
        self.game_code = code
        self.bot = bot
