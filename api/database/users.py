import sqlalchemy


from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

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
    health = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    profession = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    hobby = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    luggage = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    action_card = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    age = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    phobia = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    fact1 = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    fact2 = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    active = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        default=True
    )

    def to_json(self):
        return {
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
            "phobia": self.phobia
        }
