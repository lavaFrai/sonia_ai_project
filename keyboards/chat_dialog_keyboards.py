from aiogram.utils.keyboard import InlineKeyboardBuilder

from main import server


async def get_dialog_stop_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=server.get_string("dialog-stop"), callback_data="dialog.stop")
    return keyboard.as_markup()


async def get_dialog_resume_keyboard(dialog_id):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=server.get_string("dialog-resume"), callback_data=f"dialog.resume.{dialog_id}")
    return keyboard.as_markup()
