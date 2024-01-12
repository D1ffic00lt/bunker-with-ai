import sqlalchemy

from .db_session import SqlAlchemyBase


class Room(SqlAlchemyBase):
    __tablename__ = 'rooms'

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        unique=True,
        nullable=False
    )
    host_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=False
    )
    game_code = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
        unique=True
    )
    bunker = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    threat = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
    catastrophe = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False
    )
