from aiogram.utils.keyboard import InlineKeyboardBuilder

from main import server


async def get_non_context_action(user):
    keyboard = InlineKeyboardBuilder()
    # keyboard.button(text=user.get_string("non-context-action.generate-image"), callback_data="non-context-action.generate-image")
    # keyboard.button(text=user.get_string("non-context-action.extend-image"), callback_data="non-context-action.extend-image")
    keyboard.button(text=user.get_string("dialog-start"), callback_data="dialog.start")
    keyboard.adjust(2)
    return keyboard.as_markup()


async def get_non_context_voice_keyboard(file_data, user):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=user.get_string("non-context-action.non_context_voice.transcribe"),
                    callback_data="non_context_voice.transcribe")
    return keyboard.as_markup()


async def get_non_context_video_note_keyboard(file_data, user):
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=user.get_string("non-context-action.non_context_video_note.transcribe-audio"),
                    callback_data="non_context_video_note.transcribe-audio")
    return keyboard.as_markup()


async def get_non_context_text_keyboard(data, user):
    keyboard = InlineKeyboardBuilder()
    # keyboard.button(text=user.get_string("non-context-action.non_context_text.continue"),
    #                 callback_data="non_context_text.continue")
    keyboard.button(text=user.get_string("non-context-action.non_context_text.reduce"),
                    callback_data="non_context_text.reduce")
    # keyboard.button(text=user.get_string("non-context-action.non_context_text.vocalize"),
    #                 callback_data="non_context_text.vocalize")
    keyboard.button(text=user.get_string("non-context-action.non_context_text.grammar"),
                    callback_data="non_context_text.check_grammar")
    keyboard.adjust(2)
    return keyboard.as_markup()
