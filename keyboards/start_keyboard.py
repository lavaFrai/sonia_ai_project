import os

import yaml
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_language_list_keyboard():
    langs = os.listdir("i18n")
    langs = list(map(lambda x: load_language_name(x), langs))

    keyboard = InlineKeyboardBuilder()
    for i in langs:
        keyboard.button(text=i[1], callback_data=f"start.language_set.{i[0]}")
    keyboard.adjust(2)

    return keyboard.as_markup()


def load_language_name(name):
    with open(f"i18n/{name}", encoding='utf-8') as f:
        language_name = yaml.load(f, Loader=yaml.FullLoader)["language"]
    short_name = name.split('.')[0]
    return short_name, language_name
