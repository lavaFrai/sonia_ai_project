import enum
import json

import peewee
from aiogram.types import Message, CallbackQuery

from main import server
from models.user_cache import UserCache
from utils.migration import do_migration_for


@do_migration_for(server.db)
class User(peewee.Model):
    id = peewee.BigIntegerField(unique=True)
    language = peewee.TextField(default="en-US")
    state = peewee.IntegerField(default=0)
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

    def get_cache(self) -> dict:
        cache, _ = UserCache.get_or_create(user_id=self.id)
        return json.loads(cache.data)

    def get_cache_field(self, field, default_value):
        cache, _ = UserCache.get_or_create(user_id=self.id)
        data: dict = json.loads(cache.data)
        if field in data:
            return data[field]
        return default_value

    def set_cache_field(self, field, value):
        data: dict = self.get_cache()
        data[field] = value
        self.save_cache(data)

    def save_cache(self, data: dict):
        cache, _ = UserCache.get_or_create(user_id=self.id)
        cache.data = json.dumps(data)
        cache.save()

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
