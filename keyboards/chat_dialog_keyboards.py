from aiogram.utils.keyboard import InlineKeyboardBuilder

from main import server


async def get_dialog_stop_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=server.get_string("dialog-stop"), callback_data="dialog.stop")
    return keyboard.as_markup()
