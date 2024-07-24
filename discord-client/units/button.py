from .active_cards import *


class ControlButtons(discord.ui.View):
    ATTRIBUTES_TRANSLATE = {
        "Пол и Возраст": "age_revealed",
        "Здоровье": "health_revealed",
        "Профессия": "profession_revealed",
        "Хобби": "hobby_revealed",
        "Багаж": "luggage_revealed",
        "Факт 1": "fact1_revealed",
        "Факт 2": "fact2_revealed",
        "Фобия": "phobia_revealed",
        "Активная Карта": "action_card_revealed"
    }

    def __init__(self, code, *, bot, user_data):
        super().__init__(timeout=None)
        self.messages = []
        self.game_code = code
        self.bot = bot
        if not user_data["active"]:
            for i in self.children:
                i.disabled = True
            return
        for i in self.children:
            if i.label not in self.ATTRIBUTES_TRANSLATE:
                continue
            if user_data[self.ATTRIBUTES_TRANSLATE[i.label]]:
                i.disabled = True

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
        # TODO
        await inter.message.edit(view=self)
        # await self.send("action_card", inter.user.id)
        async with httpx.AsyncClient() as client:
            try:
                game = await client.get(
                    "http://api:9462/bunker/api/v1/get-game/{}".format(self.game_code),
                    timeout=60
                )
                if game.status_code // 100 in [4, 5]:
                    await inter.response.send_message("Что-то пошло не так...")
                    return
                game = game.json()
                response = await client.post(
                    "http://api:9462/bunker/api/v1/use-active-card/{}/{}".format(self.game_code, inter.user.id),
                    json={"user_id": inter.user.id, "switch": False},
                )
                if response.status_code == 424:
                    button.disabled = False
                    # TODO

                    await inter.message.edit(view=self)
                    if len(self.messages) != 0:
                        await inter.response.send_message("Что-то пошло не так...")
                        message = await inter.original_response()
                        await message.delete(delay=5)
                        return
                    view = ActiveCardControlButtons(self.game_code, self.bot)
                    view.original_view = self
                    view.original_message = inter.message
                    for p in game["users"]:
                        user: discord.User = await self.bot.fetch_user(p["user_id"])
                        button = ActiveCardButton(
                            label=user.name, custom_id=str(user.id) + self.bot.generate_random_code(), emoji="🪦"
                        )
                        if not p["active"] or p["user_id"] == inter.user.id:
                            button.disabled = True
                            button.custom_id = "-1" + self.bot.generate_random_code()
                        view.add_item(button)
                    button = ActiveCardButton(
                        label="Отмена", custom_id="stop_vote" + self.bot.generate_random_code()
                    )
                    view.add_item(button)
                    message = await inter.user.send("Выберите игрока", view=view)
                    view.message = message
                    self.messages.append(message)
                    try:
                        await inter.response.defer()
                    except discord.errors.NotFound:
                        pass
                    return
                if response.status_code // 100 in [4, 5]:
                    await inter.response.send_message("Что-то пошло не так...")
                    message = await inter.original_response()
                    await message.delete(delay=5)
                    return
            except httpx.TimeoutException:
                await inter.response.send_message("Что-то пошло не так...")
                message = await inter.original_response()
                await message.delete(delay=5)
                return
        await inter.response.send_message("Использовано")
        await self.send("action_card", inter.user.id)
        message = await inter.original_response()
        await message.delete(delay=5)

    @discord.ui.button(label="Выйти", style=discord.ButtonStyle.red, emoji="⚰️")  # 🪦
    async def exit_callback(self, inter: discord.Interaction, button: discord.Button):
        is_host = False
        for i in self.children:
            if i.label == "Начать голосование":
                is_host = True
                continue
            i.disabled = True

        button.style = discord.ButtonStyle.secondary
        await inter.message.edit(view=self)
        if not is_host:
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
