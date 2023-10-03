from aiogram import types


async def add_commands(bot):
    await bot.set_my_commands([
        types.bot_command.BotCommand(command="/start", description="Start the bot"),
        types.bot.command.BotCommand(command="/info", description="Show user info and balance")
    ])
