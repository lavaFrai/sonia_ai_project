import json

import peewee

from main import server
from models.chat_message import ChatMessage
from utils.migration import do_migration_for


@do_migration_for(server.db)
class ChatDialog(peewee.Model):
    id = peewee.AutoField(unique=True, primary_key=True)
    user_id = peewee.IntegerField(null=False)
    name = peewee.TextField(null=True)
    last_bot_message = peewee.IntegerField(default=0)

    class Meta:
        database = server.db

    @staticmethod
    async def get_dialog_history(dialog_id):
        """history = ChatMessage.select(ChatMessage.text, ChatMessage.role)\
            .where(ChatMessage.dialog_id == dialog_id)\
            .order_by(ChatMessage.id)
        history_json = []
        for message in history:
            history_json.append({
                "role": message.role,
                "content": message.text
            })
        return history_json"""

        return list(map(
            lambda x: json.loads(x.text),
            ChatMessage.select().where(ChatMessage.dialog_id == dialog_id)
        ))

    @staticmethod
    async def save_dialog_history(dialog_id, history):
        dialog = ChatDialog.get(id=dialog_id)
        dialog.history = json.dumps(history)
        dialog.save()

    @staticmethod
    async def add_message(dialog_id, message):
        ChatMessage.create(
            dialog_id=dialog_id,
            text=json.dumps(message)
        )

    @staticmethod
    async def add_messages(dialog_id, messages):
        for message in messages:
            await ChatDialog.add_message(dialog_id, message)
