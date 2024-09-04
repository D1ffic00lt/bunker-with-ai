import textwrap

from PIL import Image, ImageDraw, ImageFont
from copy import deepcopy


class Generator(object):
    def __init__(
        self, *,
        template_path: str, font_path: str,
        title_font_path: str,
        flag_path: str, skull_path: str
    ):
        self.template_path = template_path
        self.font_path = font_path
        self.flag_path = flag_path
        self.skull_path = skull_path
        self.template_image = Image.open(template_path).resize((1920, 1080)).convert("RGBA")
        self.width, self.height = self.template_image.size
        self.main_info_font = ImageFont.truetype(title_font_path, 100, encoding="unic")
        self.info_font = ImageFont.truetype(font_path, 45, encoding="unic")
        self.flag = Image.open(flag_path).resize((90, 90)).convert("RGBA")
        self.skull = Image.open(skull_path).resize((150, 150)).convert("RGBA")

    @staticmethod
    def draw_text_with_shadow(draw, position, text, font, fill, shadow_offset=(2, 2), shadow_fill="black"):
        shadow_position = (position[0] + shadow_offset[0], position[1] + shadow_offset[1])
        draw.text(shadow_position, text, font=font, fill=shadow_fill)
        draw.text(position, text, font=font, fill=fill)

    def generate(self, data):
        gender = data["gender"][0] if data["gender_revealed"] else "?"
        age = data["age"].split(", ")[0] if data["age_revealed"] else "?"
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
        active = data["active"]
        if votes < 0:
            votes = 0

        template_image = deepcopy(self.template_image)
        image = ImageDraw.Draw(template_image)
        change_of_offset = 10
        text_wrap_step = 50
        offset = self.height - 120

        for line in textwrap.wrap(hobby[:70], width=25)[::-1]:
            self.draw_text_with_shadow(image, (80, offset), line, self.info_font, "#f4d35f")
            offset -= text_wrap_step
        offset -= change_of_offset

        for line in textwrap.wrap(phobia[:70], width=25)[::-1]:
            self.draw_text_with_shadow(image, (80, offset), line, self.info_font, "#6ad1cd")
            offset -= text_wrap_step
        offset -= change_of_offset

        for line in textwrap.wrap(health[:70], width=25)[::-1]:
            self.draw_text_with_shadow(image, (80, offset), line, self.info_font, "#efa0e5")
            offset -= text_wrap_step
        offset -= change_of_offset

        for line in textwrap.wrap(profession[:70], width=25)[::-1]:
            self.draw_text_with_shadow(image, (80, offset), line, self.info_font, "white")
            offset -= text_wrap_step

        self.draw_text_with_shadow(image, (115, 230), gender, self.main_info_font, "#f6de8a")
        self.draw_text_with_shadow(image, (320, 230), age, self.main_info_font, "#f6de8a")

        offset = self.height - 120
        for line in textwrap.wrap(luggage[:70], width=25)[::-1]:
            self.draw_text_with_shadow(
                image, (self.width - self.info_font.getlength(line) - 80, offset),
                line, self.info_font, "#f32b7b"
            )
            offset -= text_wrap_step
        offset -= change_of_offset
        for line in textwrap.wrap(fact2[:70], width=25)[::-1]:
            self.draw_text_with_shadow(
                image, (self.width - self.info_font.getlength(line) - 80, offset),
                line, self.info_font, "#54e6a3"
            )
            offset -= text_wrap_step
        offset -= change_of_offset
        for line in textwrap.wrap(fact1[:70], width=25)[::-1]:
            self.draw_text_with_shadow(
                image, (self.width - self.info_font.getlength(line) - 80, offset),
                line, self.info_font, "#5bec5f"
            )
            offset -= text_wrap_step

        step = 100
        for i in range(votes):
            template_image.paste(self.flag, (380 + (i + 1) * step, 230), self.flag)
        if not active:
            # template_image.paste(self.skull, (template_image.size[0] - 150 - 100, 100), self.skull)
            self.draw_text_with_shadow(
                image, (self.width - self.main_info_font.getlength("ИЗГНАН") - 80, 80),
                "ИЗГНАН", self.main_info_font, "white"
            )

        return template_image


if __name__ == "__main__":
    test_data = {
        "gender_revealed": True,       "gender": "Женщина",
        "health_revealed": True,       "health": "Аллергический ринит 5%",
        "profession_revealed": True,   "profession": "Журналист-международник",
        "hobby_revealed": True,        "hobby": "Запоминать номера самолётов, пролетающих над городом",
        "luggage_revealed": True,      "luggage": "Книжка о выживании в экстремальных условиях",
        "action_card_revealed": True,  "action_card": "",
        "age_revealed": True,          "age": "76 стаж: 15 лет",
        "fact1_revealed": True,        "fact1": "Умеет играть на гитаре",
        "fact2_revealed": True,        "fact2": "Был награждён грамотой за помощь бездомным животным",
        "phobia_revealed": True,       "phobia": "Моторофобия",
        "active": False,               "number_of_votes": 3
    }
    gen = Generator(
        template_path="static/frame.png",
        font_path="./static/Montserrat-Bold.ttf",
        title_font_path="./static/Gilroy Extra Bold.otf",
        flag_path="./static/red_flag.png",
        skull_path="./static/red_skull.png"
    )
    gen.generate(test_data).save("123.png")
