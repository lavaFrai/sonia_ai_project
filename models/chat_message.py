import peewee

from main import server
from utils.migration import do_migration_for


@do_migration_for(server.db)
class ChatMessage(peewee.Model):
    id = peewee.AutoField(unique=True, primary_key=True)
    text = peewee.TextField(null=True)
    dialog_id = peewee.IntegerField()

    class Meta:
        database = server.db
