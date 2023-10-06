from aiogram.utils.keyboard import InlineKeyboardBuilder

from main import server


def get_cancel_keyboard(user):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=user.get_string("cancel"),
                    callback_data="cancel-all-actions")
    return keyboard.as_markup()
