import discord
import httpx


class ControlButtons(discord.ui.View):
    def __init__(self, code):
        super().__init__(timeout=None)
        self.game_code = code

    async def send(self, attribute, user_id):
        async with httpx.AsyncClient() as client:
            try:
                await client.patch(
                    "http://api:9462/bunker/api/v1/reveal-characteristic/{}/{}".format(
                        self.game_code, user_id
                    ),
                    json={
                        "attribute": attribute
                    }
                )
            except httpx.TimeoutException:
                pass

    @discord.ui.button(label="Пол и Возраст", style=discord.ButtonStyle.primary, emoji="👴")
    async def gender_and_age_callback(self, inter: discord.Interaction, button: discord.Button):
        button.disabled = True
        await inter.message.edit(view=self)
        await self.send("gender", inter.user.id)
        await self.send("age", inter.user.id)

        await inter.response.send_message("Вскрыто")
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Здоровье", style=discord.ButtonStyle.primary, emoji="💊")
    async def health_callback(self, inter: discord.Interaction, button: discord.Button):
        button.disabled = True
        await inter.message.edit(view=self)
        await self.send("health", inter.user.id)

        await inter.response.send_message("Вскрыто")
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Профессия", style=discord.ButtonStyle.primary, emoji="👩‍🚀")
    async def profession_callback(self, inter: discord.Interaction, button: discord.Button):
        button.disabled = True
        await inter.message.edit(view=self)
        await self.send("profession", inter.user.id)

        await inter.response.send_message("Вскрыто")
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Хобби", style=discord.ButtonStyle.primary, emoji="💻")
    async def hobby_callback(self, inter: discord.Interaction, button: discord.Button):
        button.disabled = True
        await inter.message.edit(view=self)
        await self.send("hobby", inter.user.id)

        await inter.response.send_message("Вскрыто")
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Багаж", style=discord.ButtonStyle.primary, emoji="🧳")
    async def luggage_callback(self, inter: discord.Interaction, button: discord.Button):
        button.disabled = True
        await inter.message.edit(view=self)
        await self.send("luggage", inter.user.id)

        await inter.response.send_message("Вскрыто")
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Факт 1", style=discord.ButtonStyle.primary, emoji="💌")
    async def fact1_callback(self, inter: discord.Interaction, button: discord.Button):
        button.disabled = True
        await inter.message.edit(view=self)
        await self.send("fact1", inter.user.id)

        await inter.response.send_message("Вскрыто")
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Факт 2", style=discord.ButtonStyle.primary, emoji="💌")
    async def fact2_callback(self, inter: discord.Interaction, button: discord.Button):
        button.disabled = True
        await inter.message.edit(view=self)
        await self.send("fact2", inter.user.id)

        await inter.response.send_message("Вскрыто")
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Фобия", style=discord.ButtonStyle.primary, emoji="🤡")
    async def phobia_callback(self, inter: discord.Interaction, button: discord.Button):
        button.disabled = True
        await inter.message.edit(view=self)
        await self.send("phobia", inter.user.id)
        await inter.response.send_message("Вскрыто")
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Активная Карта", style=discord.ButtonStyle.success, emoji="🎴")
    async def action_card_callback(self, inter: discord.Interaction, button: discord.Button):
        button.disabled = True
        await inter.message.edit(view=self)
        await self.send("action_card", inter.user.id)
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://api:9462/bunker/api/v1/use-active-card/{}/{}".format(self.game_code, inter.user.id)
                )
                if response.status_code // 100 in [4, 5]:
                    await inter.response.send_message("Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.response.send_message("Что-то пошло не так...")
                return
        await inter.response.send_message("Использовано")
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Выйти", style=discord.ButtonStyle.red, emoji="⚰️")  # 🪦
    async def exit_callback(self, inter: discord.Interaction, button: discord.Button):
        for i in self.children:
            i.disabled = True

        button.style = discord.ButtonStyle.secondary
        await inter.message.edit(view=self)
        self.stop()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    "http://api:9462/bunker/api/v1/leave-game/{}/{}".format(self.game_code, inter.user.id)
                )
                if response.status_code // 100 in [4, 5]:
                    await inter.response.send_message("Что-то пошло не так...")
                    return
            except httpx.TimeoutException:
                await inter.response.send_message("Что-то пошло не так...")
                return
        await inter.response.send_message("Вы вышли из игры")
