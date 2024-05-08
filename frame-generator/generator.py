from PIL import Image, ImageDraw, ImageFont
from copy import deepcopy


class Generator(object):
    def __init__(self, template_path: str, font_path: str):
        self.template_path = template_path
        self.font_path = font_path
        self.template_image = Image.open(template_path)
        self.width, self.height = self.template_image.size
        self.main_info_font = ImageFont.truetype(font_path, 100, encoding="unic")
        self.info_font = ImageFont.truetype(font_path, 50, encoding="unic")

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

        template_image = deepcopy(self.template_image)
        image = ImageDraw.Draw(template_image)
        image.text((160, 210), gender, fill="#f6de8a", font=self.main_info_font)
        image.text((340, 210), age, fill="#f6de8a", font=self.main_info_font)

        image.text((140, 790), profession, fill="white", font=self.info_font)
        image.text((140, 790 + 50), health, fill="#efa0e5", font=self.info_font)
        image.text((140, 790 + 50 * 2), phobia, fill="#6ad1cd", font=self.info_font)
        image.text((140, 790 + 50 * 3), hobby, fill="#f4d35f", font=self.info_font)

        image.text(
            (self.width - self.info_font.getlength(fact1) - 120, 840),
            fact1, fill="#5bec5f", font=self.info_font
        )
        image.text(
            (self.width - self.info_font.getlength(fact2) - 120, 890),
            fact2, fill="#54e6a3", font=self.info_font
        )
        image.text(
            (self.width - self.info_font.getlength(luggage) - 120, 940),
            luggage, fill="#f32b7b", font=self.info_font
        )
        return template_image
