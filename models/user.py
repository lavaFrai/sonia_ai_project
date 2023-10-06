import enum

import peewee
from aiogram.types import Message, CallbackQuery

from main import server
from utils.migration import do_migration_for


@do_migration_for(server.db)
class User(peewee.Model):
    id = peewee.IntegerField(unique=True)
    language = peewee.TextField(default="en-US")
    state = peewee.IntegerField(default=1)
    subscription_expires = peewee.TimestampField(default=0)

    @staticmethod
    def get_by_tg_id(tg_id: int):
        user = User.get_or_none(id=tg_id)
        if user is None:
            ...
        else:
            return user

    @staticmethod
    def get_by_message(msg: Message):
        return User.get_by_tg_id(msg.from_user.id)

    @staticmethod
    def get_by_callback(cb: CallbackQuery):
        return User.get_by_tg_id(cb.from_user.id)

    def get_string(self, name):
        return server.get_string(name, self.language)

    class State:
        language_select = 0
        ready = 1

    class Meta:
        database = server.db
