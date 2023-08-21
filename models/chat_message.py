import peewee

from main import server
from utils.migration import do_migration_for


@do_migration_for(server.db)
class State(peewee.Model):
    key = peewee.TextField()
    value = peewee.TextField(null=True)

    class Meta:
        database = server.db
