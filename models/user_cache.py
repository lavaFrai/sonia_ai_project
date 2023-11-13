import peewee
from aiogram.types import Message, CallbackQuery

from main import server
from utils.migration import do_migration_for


@do_migration_for(server.db)
class UserCache(peewee.Model):
    user_id = peewee.IntegerField(unique=True)
    data = peewee.TextField(default="{}")

    class Meta:
        database = server.db
