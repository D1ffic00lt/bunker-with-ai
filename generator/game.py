import random

from copy import deepcopy

from config import active_cards


class Game(object):
    def __init__(self):
        self.active_cards = deepcopy(active_cards)
        self.health = []
        self.professions = []

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
        self.health.append(data["health"])
        self.professions.append(data["profession"])

    def get_promt(self, template):
        template = template.replace("<healths>", str(self.health))
        template = template.replace("<professions>", str(self.professions))
        return template
