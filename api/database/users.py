import sqlalchemy

from sqlalchemy.ext.hybrid import hybrid_method

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'
    REVEL_ATTRIBUTES = [
        "gender_revealed", "health_revealed",
        "profession_revealed", "hobby_revealed",
        "luggage_revealed", "action_card_revealed",
        "age_revealed", "fact1_revealed",
        "fact2_revealed", "phobia_revealed"
    ]
    ATTRIBUTES_TRANSLATE = {
        "Здоровье": "health",
        "Гендер": "gender",
        "Профессия": "profession",
        "Хобби": "hobby",
        "Багаж": "luggage"
    }

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        unique=True,
        nullable=False
    )
    room_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('rooms.id')
    )
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer
    )
    gender = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    gender_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    health = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    health_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    profession = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    profession_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    hobby = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    hobby_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    luggage = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    luggage_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    action_card = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    action_card_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    age = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    age_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    phobia = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    phobia_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    fact1 = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    fact1_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    fact2 = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    fact2_revealed = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=False
    )
    active = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=True
    )
    number_of_votes = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=False,
        default=0
    )

    def to_json(self):
        return {
            "user_id": self.user_id,
            "room_id": self.room_id,
            "gender": self.gender,
            "health": self.health,
            "profession": self.profession,
            "hobby": self.hobby,
            "luggage": self.luggage,
            "action_card": self.action_card,
            "age": self.age,
            "fact1": self.fact1,
            "fact2": self.fact2,
            "active": self.active,
            "phobia": self.phobia,
            "gender_revealed": self.gender_revealed,
            "health_revealed": self.health_revealed,
            "profession_revealed": self.profession_revealed,
            "hobby_revealed": self.hobby_revealed,
            "luggage_revealed": self.luggage_revealed,
            "action_card_revealed": self.action_card_revealed,
            "age_revealed": self.age_revealed,
            "fact1_revealed": self.fact1_revealed,
            "fact2_revealed": self.fact2_revealed,
            "phobia_revealed": self.phobia_revealed,
            "number_of_votes": self.number_of_votes
        }

    @hybrid_method
    def get_attr(self, attribute, *, revealed=False):
        if attribute not in self.ATTRIBUTES_TRANSLATE:
            return
        attribute = self.ATTRIBUTES_TRANSLATE[attribute]
        if revealed:
            attribute += "_revealed"
        return getattr(self, attribute)

    @hybrid_method
    def set_attr(self, attribute, value):
        if attribute not in self.ATTRIBUTES_TRANSLATE:
            return
        setattr(self, self.ATTRIBUTES_TRANSLATE[attribute], value)

    def update(self, attribute):
        if attribute not in self.REVEL_ATTRIBUTES:
            return
        setattr(self, attribute, True)
