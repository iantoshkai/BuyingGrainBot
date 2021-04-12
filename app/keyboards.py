import typing
from dataclasses import dataclass

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


@dataclass
class ListOfButtons:
    text: typing.List
    callback: typing.List = None
    align: typing.List[int] = None

    @property
    def inline_keyboard(self):
        return generate_inline_keyboard(self)

    @property
    def reply_keyboard(self):
        return generate_reply_keyboard(self)


def generate_inline_keyboard(args: ListOfButtons) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup()
    if args.text and args.callback and not (len(args.text) == len(args.callback)):
        raise IndexError("Все списки должны быть одной длины!")

    if not args.align:
        for num, button in enumerate(args.text):
            keyboard.add(InlineKeyboardButton(text=str(button),
                                              callback_data=str(args.callback[num])))
    else:
        count = 0
        for row_size in args.align:
            keyboard.row(*[InlineKeyboardButton(text=str(text), callback_data=str(callback_data))
                           for text, callback_data in
                           tuple(zip(args.text, args.callback))[count:count + row_size]])
            count += row_size
    return keyboard


def generate_reply_keyboard(args: ListOfButtons) -> ReplyKeyboardMarkup:
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    if not args.align:
        for num, button in enumerate(args.text):
            keyboard.add(KeyboardButton(text=str(button)))
    else:
        count = 0
        for row_size in args.align:
            keyboard.row(*[KeyboardButton(text=str(text)) for text in args.text[count:count + row_size]])
            count += row_size
    return keyboard


hide_markup = ReplyKeyboardRemove()


def phone_number_keyboard():
    k = ReplyKeyboardMarkup(resize_keyboard=True)
    k.insert(KeyboardButton('Відправити📱', request_contact=True))
    return k


def menu():
    k = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    k.insert(KeyboardButton('🌾 Рух зерна по елеватору'))
    k.insert(KeyboardButton('📦 Загальні залишки елеватора'))
    return k


def detailing():
    k = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    k.insert(KeyboardButton('🗃 Загальна'))
    k.insert(KeyboardButton('🗂 По контрагентам'))
    k.insert(KeyboardButton('⬅️ Назад'))
    return k

def back():
    k = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    k.insert(KeyboardButton('⬅️ Назад'))
    return k
