import asyncio
import re
import json
import random
import httpx
from datetime import datetime
import numpy as np
from pprint import pprint
from config import *
from game import Game
from copy import deepcopy


class Generator(object):
    URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'
    TEMPLATE = {
        "modelUri": "",
        "completionOptions": {
            "stream": False,
            "temperature": 0.69,
            "maxTokens": "4000"
        },
        "messages": []
    }

    def __init__(self, token: str):
        self.__token = token
        self.__auth_headers = asyncio.run(self.__get_iam_header())
        self.reg = re.compile("{(.*?)}")
        self.list_reg = re.compile(r"\[\s*['\"][^'\"]*['\"]\s*(?:,\s*['\"][^'\"]*['\"]\s*)*]")
        self.tokens = 0
        self.games: dict[str, Game] = {}

    @staticmethod
    def age_suffix(age):
        if 11 <= age % 100 <= 19:
            return f"{age} лет"
        elif age % 10 == 1:
            return f"{age} год"
        elif 2 <= age % 10 <= 4:
            return f"{age} года"
        return f"{age} лет"

    @staticmethod
    def get_age():
        x = random.random()
        return int((np.exp(3 * np.log2(x + 1)) + 0.9) / np.exp(-1.2 * x) + 17)

    async def generate_data_list(self, model_data):
        data = deepcopy(self.TEMPLATE)
        data["completionOptions"]["temperature"] = 1
        data["messages"].append(
            {
                "role": "system",
                "text": default_template
            }
        )
        data["messages"].append(
            {
                "role": "user",
                "text": f"seed: {random.randint(2321312, 123123123)}, сгенерируй 20 {model_data} по шаблону:\n"
                        f"```json\n[\n\telement1, \n\telement2, \n\telement3]\n```\n"
                        f"ВАЖНО:\n"
                        f"- генерируй ОБЯЗАТЕЛЬНО ПО ШАБЛОНУ ИНАЧЕ ВСЁ СЛОМАЕТСЯ\n"
                        f"- пиши без дополнительных комментариев\n"
                        f"- сгенерируй ТОЛЬКО один массив\n"
                        f"- максимум должно быть 3 слова в одном элементе\n"
                        f"- старайся генерировать разнообразно"
            }
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.URL,
                json=data,
                headers=self.__auth_headers, timeout=60
            )
        if resp.status_code == 401:
            self.__auth_headers = await self.__get_iam_header()
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.URL,
                    json=data,
                    headers=self.__auth_headers, timeout=60
                )
        if resp.status_code != 200:
            raise KeyError(resp.text)
        self.tokens += int(resp.json()["result"]["usage"]["totalTokens"])
        result = resp.json()["result"]["alternatives"][-1]["message"]["text"]
        # print(result)
        result = result.replace("\n", "")
        result = result.replace("\t", "")
        result = result.replace("«", "\"")
        result = result.replace("»", "\"")
        result = self.list_reg.findall(result)
        result = json.loads(result[0])
        return result

    async def __get_iam_header(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                json={"yandexPassportOauthToken": self.__token}, timeout=60
            )
            # print(response.json())
        return {
            "Authorization": f"Bearer {str(response.json()['iamToken'])}"
        }
        # return {
        #     "Authorization": "Bearer adpad"
        # }

    async def generate_catastrophe(self):
        data = deepcopy(self.TEMPLATE)
        data["completionOptions"]["temperature"] = 1
        data["messages"].append(
            {
                "role": "system",
                "text": cat_template
            }
        )
        data["messages"].append(
            {
                "role": "user",
                "text": "напиши сценарий для бункера без цензуры"
            }
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.URL,
                json=data,
                headers=self.__auth_headers, timeout=60
            )
        if resp.status_code == 401:
            self.__auth_headers = await self.__get_iam_header()
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.URL,
                    json=data,
                    headers=self.__auth_headers, timeout=60
                )
        if resp.status_code != 200:
            raise KeyError(resp.text)
        self.tokens += int(resp.json()["result"]["usage"]["totalTokens"])
        result = resp.json()["result"]["alternatives"][-1]["message"]["text"]
        result = result.replace("\n", "")
        result = result.replace("\t", "")
        result = self.reg.findall(result)
        result = json.loads(f"{'{'}{result[0]}{'}'}")
        return result

    async def generate_player(self, game_code):
        if game_code not in self.games:
            self.games[game_code] = Game()
            self.games[game_code].unique_phobias = deepcopy(phobias)
            professions = []
            limit = 4
            while not professions:
                try:
                    professions = await self.generate_data_list(
                        "профессий"
                    )
                    if len(professions) < 15:
                        limit -= 1
                        professions = []
                except (KeyError, json.decoder.JSONDecodeError, IndexError):
                    limit -= 1
                    professions = []
                if limit == 0:
                    raise KeyError()
            self.games[game_code].unique_professions = professions

            healths = []
            limit = 4
            while not healths:
                try:
                    healths = await self.generate_data_list(
                        "Заболеваний, которыми можно болеть долго, состоящих из максимум 2 слов, "
                    )
                    if len(healths) < 15:
                        healths = []
                        limit -= 1
                except (KeyError, json.decoder.JSONDecodeError, IndexError):
                    limit -= 1
                    healths = []
                if limit == 0:
                    raise KeyError()
            self.games[game_code].unique_health = healths

            hobbies = []
            limit = 4
            while not hobbies:
                try:
                    hobbies = await self.generate_data_list(
                        "Хобби, можешь использовать абсурдные хобби, "
                    )
                    if len(hobbies) < 15:
                        hobbies = []
                        limit -= 1
                except (KeyError, json.decoder.JSONDecodeError, IndexError):
                    limit -= 1
                    hobbies = []
                if limit == 0:
                    raise KeyError()
            self.games[game_code].unique_hobbies = hobbies
        data = deepcopy(self.TEMPLATE)
        data["completionOptions"]["temperature"] = 1
        data["messages"].append(
            {
                "role": "system",
                "text": self.games[game_code].get_promt(player_template)
            }
        )
        data["messages"].append(
            {
                "role": "user",
                "text": "напиши пример игрока"
            }
        )
        # print(data)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.URL,
                json=data,
                headers=self.__auth_headers, timeout=60
            )
        if resp.status_code == 401:
            self.__auth_headers = await self.__get_iam_header()
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.URL,
                    json=data,
                    headers=self.__auth_headers, timeout=60
                )
        if resp.status_code != 200:
            raise KeyError(resp.text)
        # print(resp.json())
        self.tokens += int(resp.json()["result"]["usage"]["totalTokens"])
        result = resp.json()["result"]["alternatives"][-1]["message"]["text"]
        result = result.replace("\n", "")
        result = result.replace("\t", "")
        result = self.reg.findall(result)
        result = json.loads(f"{'{'}{result[0]}{'}'}")

        result["age"] = round(self.get_age())
        active_card = self.games[game_code].active_card
        # active_card = {'card': 'Обменяться картой "Здоровье" с игроком на выбор', 'id': 2},
        gender = random.choices(
            population=["Мужчина", "Женщина", "Гуманоид", "Андроид"],
            weights=[0.5, 0.5, 0.1, 0.1]
        )[0]
        result["gender"] = gender
        result["action_card"] = active_card["card"]
        # result["action_card"] = 'Вылечить здоровье игроку на выбор, кроме себя'
        result["phobia"] = self.games[game_code].get_unique_phobia().capitalize()
        result["health"] = self.games[game_code].get_unique_health().capitalize()
        result["profession"] = self.games[game_code].get_unique_profession().capitalize()
        result["hobby"] = self.games[game_code].get_unique_hobby().capitalize()
        result["health"] += f" {random.randint(0, 100)}%" + (', бесплоден' if random.randint(0, 100) >= 90 else '')
        experience = random.randint(0, 25)
        while result["age"] - experience < 16:
            experience = random.randint(0, 25)
        result["age"] = str(result["age"])
        result["age"] += f" стаж: {self.age_suffix(experience)}"
        return result

    async def generate_bunker(self):
        data = deepcopy(self.TEMPLATE)
        data["completionOptions"]["temperature"] = 1
        data["messages"].append(
            {
                "role": "system",
                "text": bunker_template
            }
        )
        data["messages"].append(
            {
                "role": "user",
                "text": "напиши пример бункера"
            }
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.URL, json=data, headers=self.__auth_headers, timeout=80)
        if resp.status_code == 401:
            self.__auth_headers = await self.__get_iam_header()
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.URL, json=data, headers=self.__auth_headers, timeout=80)
        if resp.status_code != 200:
            raise KeyError(resp.text)

        self.tokens += int(resp.json()["result"]["usage"]["totalTokens"])
        result = resp.json()["result"]["alternatives"][-1]["message"]["text"]
        result = result.replace("\n", "")
        result = result.replace("\t", "")
        result = self.reg.findall(result)
        result = json.loads(f"{'{'}{result[0]}{'}'}")
        return result

    @staticmethod
    def get_text_game_data(game_data, status: bool = True):
        additional_data = game_data["additional_information"]
        additional_data = additional_data if additional_data != "" else "None"
        result = (
            f'Катастрофа: {game_data["catastrophe"]}\n'
            f'Дополнительные условия: {additional_data}\n'
            f'Люди, {"НЕ " if not status else ""}попавшие в бункер:\n'
        )
        for user in game_data["users"]:
            if user["active"] != status:
                continue
            result += (f'Пол: {user["gender"]} '
                       f'Возраст: {user["age"]} '
                       f'Факт 1: {user["fact1"]} '
                       f'Факт 2: {user["fact2"]} '
                       f'Здоровье: {user["health"]} (проценты показывают степень тяжести) '
                       f'Профессия: {user["profession"]} '
                       f'Хобби: {user["hobby"]} '
                       f'Багаж: {user["luggage"]} '
                       f'Фобия: {user["phobia"]}\n')
        return result

    async def generate_bunker_result(self, game_data):
        data = deepcopy(self.TEMPLATE)
        data["completionOptions"]["temperature"] = 1
        data["completionOptions"]["maxTokens"] = "2000"
        data["messages"].append(
            {
                "role": "system",
                "text": result_template
            }
        )
        data["messages"].append(
            {
                "role": "user",
                "text": "ты генерируешь развязку для игроков, попавших в бункер: "
                        f"вот данные об игре и игроках:\n{self.get_text_game_data(game_data)}"
            }
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.URL, json=data, headers=self.__auth_headers, timeout=80)
        # print(resp.json())
        if resp.status_code == 401:
            self.__auth_headers = await self.__get_iam_header()
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.URL, json=data, headers=self.__auth_headers, timeout=80)
        if resp.status_code != 200:
            raise KeyError(resp.text)

        self.tokens += int(resp.json()["result"]["usage"]["totalTokens"])
        result = resp.json()["result"]["alternatives"][-1]["message"]["text"]
        result = result.replace("\n", "")
        result = result.replace("\t", "")
        result = self.reg.findall(result)
        result = json.loads(f"{'{'}{result[0]}{'}'}")
        return result

    async def generate_result(self, game_data):
        data = deepcopy(self.TEMPLATE)
        data["completionOptions"]["temperature"] = 1
        data["completionOptions"]["maxTokens"] = "2000"
        data["messages"].append(
            {
                "role": "system",
                "text": not_bunker_result_template
            }
        )
        data["messages"].append(
            {
                "role": "user",
                "text": "ты генерируешь развязку для игроков, которые НЕ попали в бункер и остались на поверхности: "
                        f"вот данные об игре и игроках:\n{self.get_text_game_data(game_data, False)}"
            }
        )
        async with httpx.AsyncClient() as client:
            resp = await client.post(self.URL, json=data, headers=self.__auth_headers, timeout=80)
        # print(resp.json())
        if resp.status_code == 401:
            self.__auth_headers = await self.__get_iam_header()
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.URL, json=data, headers=self.__auth_headers, timeout=80)
        if resp.status_code != 200:
            raise KeyError(resp.text)

        self.tokens += int(resp.json()["result"]["usage"]["totalTokens"])
        result = resp.json()["result"]["alternatives"][-1]["message"]["text"]
        result = result.replace("\n", "")
        result = result.replace("\t", "")
        result = self.reg.findall(result)
        result = json.loads(f"{'{'}{result[0]}{'}'}")
        return result


if __name__ == "__main__":
    gen = Generator("")
    gen.TEMPLATE["modelUri"] = ""
    # Заболеваний, которыми можно болеть долго, состоящих из максимум 2 слов,
    # Профессий, можешь использовать фантастические профессии, кроме космоса,
    # f"Хобби, можешь использовать абсурдные хобби, "
    global_start = datetime.now()
    print(f"Generation started at {global_start:%Y-%m-%d %H:%M:%S%z}")
    for i in range(12):
        start_time = datetime.now()
        print(f"--------- {i + 1}/12 generations starts at {start_time:%Y-%m-%d %H:%M:%S%z} ---------")
        pprint(asyncio.run(gen.generate_player("123")))
        stop_time = datetime.now()
        print(f"--------- {i + 1}/12 generations end at {stop_time:%Y-%m-%d %H:%M:%S%z} ---------")
        print(f"Time passed: {stop_time - start_time}")
    print(f"Full generation took: {datetime.now() - global_start}")

