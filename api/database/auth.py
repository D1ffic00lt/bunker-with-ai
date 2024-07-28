import hashlib
import sqlalchemy

from datetime import datetime, timedelta
from sqlalchemy.ext.hybrid import hybrid_method
from uuid import uuid4

from .db_session import SqlAlchemyBase


class Auth(SqlAlchemyBase):
    __tablename__ = 'auth'
    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        unique=True,
        nullable=False
    )
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        nullable=True
    )
    date_of_creation = sqlalchemy.Column(
        sqlalchemy.String,
        default=lambda: datetime.now().strftime("%x %X"),
        nullable=False
    )
    expiration_date = sqlalchemy.Column(
        sqlalchemy.String,
        default=lambda: (datetime.now() + timedelta(days=1)).strftime("%x %X"),
        nullable=False
    )
    token_hash = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
        unique=True
    )

    @hybrid_method
    def check_expiration(self):
        return self.to_datetime(str(self.expiration_date)) > datetime.now()

    @staticmethod
    def generate_token() -> str:
        return str(uuid4())

    @staticmethod
    def hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def to_datetime(date: str) -> datetime:
        return datetime.strptime(date, "%x %X")

    def auth(self, user_id: int):
        if self.user_id is not None:
            if user_id != self.user_id:
                return {
                    "auth": False,
                    "message": "Token user_id is not equal to user id."
                }, 400

        if not self.check_expiration():
            return {
                "auth": False,
                "message": "Token expired."
            }, 401

        self.user_id = user_id
        return self.get_main_info(), 200

    def get_main_info(self):
        return {
            "auth": True,
            "user_id": self.user_id,
            "date_of_creation": self.date_of_creation,
            "expiration_date": self.expiration_date
        }
