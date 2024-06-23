import discord
import httpx

from discord import Interaction


class ActiveCardButton(discord.ui.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def callback(self, inter: Interaction):
        if self.custom_id.split("/")[0] == "-1":
            self.disabled = True
            return
        if self.custom_id.split("/")[0] == "stop_vote":
            self.view.original_view.messages = []
            await self.view.original_message.edit(view=self.view.original_view)
            try:
                await self.view.message.delete()
            except discord.errors.HTTPException:
                pass
        else:
            async with httpx.AsyncClient() as client:
                try:
                    await client.patch(
                        "http://api:9462/bunker/api/v1/reveal-characteristic/{}/{}".format(
                            self.view.game_code, inter.user.id
                        ),
                        json={
                            "attribute": "action_card"
                        }
                    )
                except httpx.TimeoutException:
                    return
                try:
                    response = await client.post(
                        "http://api:9462/bunker/api/v1/use-active-card/{}/{}".format(
                            self.view.game_code, inter.user.id
                        ),
                        json={
                            "user_id": self.custom_id.split("/")[0], "switch": True
                        }
                    )
                    for i in self.view.original_view.children:
                        if i.label == "Активная Карта":
                            i.disabled = True
                            break
                    await self.view.original_message.edit(view=self.view.original_view)
                    if response.status_code // 100 in [4, 5]:
                        message = await inter.user.send("Что-то пошло не так...")
                        await message.delete(delay=5)
                        return
                except httpx.TimeoutException:
                    message = await inter.user.send("Что-то пошло не так...")
                    await message.delete(delay=5)
                    return
            await self.view.message.delete()
            message = await inter.user.send("Использовано")
            self.disabled = True
            await message.delete(delay=2)


class ActiveCardControlButtons(discord.ui.View):
    def __init__(self, code, bot):
        super().__init__(timeout=None)
        self.message = None
        self.original_message = None
        self.original_view = None
        self.game_code = code
        self.bot = bot
