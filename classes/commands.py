from aiogram import Bot
from aiogram.types import BotCommand


class CommandsRegistrator:
    commands = {
        "start": "Clear context and restart bot",
        "language": "Change bot language",
        "image_model": "Choose image generator",
        "diagnostics": "Debug stats info",
    }

    async def update(self, bot: Bot):
        bot_commands = []
        for command in self.commands:
            bot_commands.append(BotCommand(command=f"/{command}", description=self.commands[command]))
        await bot.set_my_commands(bot_commands)
