from aiogram.utils.keyboard import InlineKeyboardBuilder

from main import server


async def get_non_context_action():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=server.get_string("non-context-action.generate-image"), callback_data="non-context-action.generate-image")
    keyboard.button(text=server.get_string("non-context-action.extend-image"), callback_data="non-context-action.extend-image")
    return keyboard.as_markup()


async def get_non_context_voice_keyboard(file_data):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=server.get_string("non-context-action.non_context_voice.transcribe"),
                    callback_data="non_context_voice.transcribe")
    return keyboard.as_markup()
