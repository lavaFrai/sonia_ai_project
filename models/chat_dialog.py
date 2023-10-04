import peewee

from main import server
from models.chat_message import ChatMessage
from utils.migration import do_migration_for


@do_migration_for(server.db)
class ChatDialog(peewee.Model):
    id = peewee.IntegerField(unique=True, primary_key=True)
    user_id = peewee.IntegerField(null=False)
    name = peewee.TextField(null=True)

    class Meta:
        database = server.db

    @staticmethod
    async def get_dialog_history(dialog_id):
        history = ChatMessage.select(ChatMessage.text, ChatMessage.role)\
            .where(ChatMessage.dialog_id == dialog_id)\
            .order_by(ChatMessage.id)
        history_json = []
        for message in history:
            history_json.append({
                "role": message.role,
                "content": message.text
            })
        return history_json
