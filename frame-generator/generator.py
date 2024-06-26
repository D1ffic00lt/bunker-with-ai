import textwrap

from PIL import Image, ImageDraw, ImageFont
from copy import deepcopy


class Generator(object):
    def __init__(self, *, template_path: str, font_path: str, flag_path: str):
        self.template_path = template_path
        self.font_path = font_path
        self.flag_path = flag_path
        self.template_image = Image.open(template_path)
        self.width, self.height = self.template_image.size
        self.main_info_font = ImageFont.truetype(font_path, 100, encoding="unic")
        self.info_font = ImageFont.truetype(font_path, 60, encoding="unic")
        self.flag = Image.open(flag_path).resize((90, 90)).convert("RGBA")

    def generate(self, data):
        gender = data["gender"][0] if data["gender_revealed"] else "?"
        age = data["age"].split()[0] if data["age_revealed"] else "?"
        profession = data["profession"].lower() if data["profession_revealed"] else "профессия"
        if data["profession_revealed"] and data["age_revealed"]:
            profession += data["age"].split("стаж:")[-1].lower()
        health = data["health"].lower() if data["health_revealed"] else "здоровье"
        luggage = data["luggage"].lower() if data["luggage_revealed"] else "багаж"
        fact1 = data["fact1"].lower() if data["fact1_revealed"] else "факт 1"
        fact2 = data["fact2"].lower() if data["fact2_revealed"] else "факт 2"
        phobia = data["phobia"].lower() if data["phobia_revealed"] else "фобия"
        hobby = data["hobby"].lower() if data["hobby_revealed"] else "хобби"
        votes = data["number_of_votes"]
        if votes < 0:
            votes = 0

        template_image = deepcopy(self.template_image)
        image = ImageDraw.Draw(template_image)
        offset = self.height - 150
        for line in textwrap.wrap(hobby[:70], width=30)[::-1]:
            image.text(
                (140, offset), line, font=self.info_font, fill="#f4d35f"
            )
            offset -= 60
        offset -= 10

        for line in textwrap.wrap(phobia[:70], width=30)[::-1]:
            image.text(
                (140, offset), line, font=self.info_font, fill="#6ad1cd"
            )
            offset -= 60
        offset -= 10

        for line in textwrap.wrap(health[:70], width=30)[::-1]:
            image.text(
                (140, offset), line, font=self.info_font, fill="#efa0e5"
            )
            offset -= 60
        offset -= 10

        for line in textwrap.wrap(profession[:70], width=30)[::-1]:
            image.text(
                (140, offset), line, font=self.info_font, fill="white"
            )
            offset -= 60
        image.text((160, 210), gender, fill="#f6de8a", font=self.main_info_font)
        image.text((340, 210), age, fill="#f6de8a", font=self.main_info_font)

        offset = self.height - 150
        for line in textwrap.wrap(luggage[:70], width=25)[::-1]:
            image.text(
                (self.width - self.info_font.getlength(line) - 120, offset), line, font=self.info_font, fill="#f32b7b"
            )
            offset -= 60
        offset -= 10
        for line in textwrap.wrap(fact2[:70], width=25)[::-1]:
            image.text(
                (self.width - self.info_font.getlength(line) - 120, offset), line, font=self.info_font, fill="#54e6a3"
            )
            offset -= 60
        offset -= 10
        for line in textwrap.wrap(fact1[:70], width=25)[::-1]:
            image.text(
                (self.width - self.info_font.getlength(line) - 120, offset), line, font=self.info_font, fill="#5bec5f"
            )
            offset -= 60
        step = 100
        for i in range(votes):
            template_image.paste(self.flag, (380 + (i + 1) * step, 225), self.flag)
        return template_image


if __name__ == "__main__":
    test_data = {
        "gender_revealed": False,       "gender": "",
        "health_revealed": False,       "health": "",
        "profession_revealed": False,   "profession": "",
        "hobby_revealed": False,        "hobby": "",
        "luggage_revealed": False,      "luggage": "",
        "action_card_revealed": False,  "action_card": "",
        "age_revealed": False,          "age": "",
        "fact1_revealed": False,        "fact1": "",
        "fact2_revealed": False,        "fact2": "",
        "phobia_revealed": False,       "phobia": "",
        "active": True,                 "number_of_votes": 0
    }
    gen = Generator(
        template_path="./static/SQUADBUNKERWEBKA.png",
        font_path="./static/Gilroy Extra Bold.otf",
        flag_path="./static/red_flag.png"
    )
    gen.generate(test_data).save("123.png")
