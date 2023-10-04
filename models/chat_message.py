import peewee

from main import server
from utils.migration import do_migration_for


@do_migration_for(server.db)
class ChatMessage(peewee.Model):
    id = peewee.IntegerField(unique=True, primary_key=True)
    role = peewee.TextField(null=False, default="user")
    text = peewee.TextField(null=True)
    dialog_id = peewee.IntegerField()

    class Meta:
        database = server.db
