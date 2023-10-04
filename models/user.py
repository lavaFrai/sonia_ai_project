import peewee

from main import server
from utils.migration import do_migration_for


@do_migration_for(server.db)
class User(peewee.Model):
    id = peewee.IntegerField(unique=True)
    subscription_expires = peewee.TimestampField(default=0)

    @staticmethod
    def get_by_tg_id(tg_id: int):
        user = User.get_or_none(id=tg_id)
        if user is None:
            ...
        else:
            return user

    class Meta:
        database = server.db
