import random

from copy import deepcopy

from config import active_cards


class Game(object):
    def __init__(self):
        self.active_cards = deepcopy(active_cards)
        self.health = []
        self.professions = []
        self.unique_professions = []
        self.unique_health = []
        self.unique_hobbies = []
        self.unique_phobias = []

    def get_unique_profession(self) -> str:
        # print(self.unique_professions)
        profession = random.choice(self.unique_professions)
        del self.unique_professions[self.unique_professions.index(profession)]
        return profession

    def get_unique_health(self) -> str:
        # print(self.unique_health)
        random_health = random.choice(self.unique_health)
        del self.unique_health[self.unique_health.index(random_health)]
        return random_health

    def get_unique_hobby(self) -> str:
        # print(self.unique_hobbies)
        hobby = random.choice(self.unique_hobbies)
        del self.unique_hobbies[self.unique_hobbies.index(hobby)]
        return hobby

    def get_unique_phobia(self) -> str:
        # print(self.unique_hobbies)
        phobia = random.choice(self.unique_phobias)
        del self.unique_phobias[self.unique_phobias.index(phobia)]
        return phobia

    @property
    def active_card(self):
        return random.choice(self.active_cards)

    def add_user_data(self, data: dict):
        for i in range(len(self.active_cards)):
            if self.active_cards[i] == data["action_card"]:
                del self.active_cards[i]
                break
        if len(self.active_cards) == 0:
            self.active_cards = deepcopy(active_cards)
        self.health.append(data["health"].split("%")[0][:-2])
        self.professions.append(data["profession"])

    def get_promt(self, template):
        template = template.replace("<healths>", str(self.health))
        template = template.replace("<professions>", str(self.professions))
        return template
