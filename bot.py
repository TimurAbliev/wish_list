import asyncio
import json
import aiofiles

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart

from config import BOT_TOKEN

GIFT_LINKS = {
    "Коньки роликовые": "https://ozon.ru/t/DLVD8ua",
    "3-D ручка": "https://ozon.ru/t/8USOqcW",
    "Набор опытов (мини-ферма)": "https://ozon.ru/t/zDSzHm7",
    "Халат": "https://ozon.ru/t/Ash7v3j",
    "Пижама": "https://ozon.ru/t/j9ytwSh",
    "Сертификат_Озон_2": "https://ozon.ru/t/Q1CwIki",
    "Сертификат_Озон_3": "https://ozon.ru/t/vIlAHMF"
}

BOOKINGS_FILE = 'storage.json'


async def load_bookings():
    async with aiofiles.open(BOOKINGS_FILE, mode='r') as f:
        content = await f.read()
        return json.loads(content)


async def save_bookings(data):
    async with aiofiles.open(BOOKINGS_FILE, mode='w') as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))


def user_already_chosen(user_id: int, bookings: dict) -> bool:
    return str(user_id) in bookings.get("confirmed_users", [])


async def on_start(message: Message):
    bookings = await load_bookings()

    if user_already_chosen(message.from_user.id, bookings):
        await message.answer("Ты уже выбрал подарок)) Встретимся на празднике!))")
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Посмотреть виш лист", callback_data="view_list")]
        ]
    )
    await message.answer(
        "Привет, это чат-бот с виш-листом подарков на день рождение Амалии. "
        "Тут ты можешь выбрать подарок из виш-листа и забронировать его! "
        "Естественно ты можешь купить что угодно не из списка и мы будем очень рады любому подарку 😊",
        reply_markup=kb
    )


async def on_view_list(callback: CallbackQuery):
    bookings = await load_bookings()
    if user_already_chosen(callback.from_user.id, bookings):
        await callback.message.answer("Ты уже выбрал подарок)) Встретимся на празднике!))")
        return

    buttons = []
    for gift, url in GIFT_LINKS.items():
        if bookings.get("bookings", {}).get(gift) is None:
            buttons.append([InlineKeyboardButton(text=gift, url=url)])

    buttons.append([InlineKeyboardButton(text="Забронировать подарок", callback_data="reserve")])
    buttons.append([InlineKeyboardButton(text="Куплю другой подарок", callback_data="other_gift")])

    await callback.message.answer("Выберите подарок из списка:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


async def on_reserve(callback: CallbackQuery):
    bookings = await load_bookings()
    if user_already_chosen(callback.from_user.id, bookings):
        await callback.message.answer("Ты уже выбрал подарок)) Встретимся на празднике!))")
        return

    buttons = []
    for gift in GIFT_LINKS.keys():
        if bookings.get("bookings", {}).get(gift) is None:
            buttons.append([InlineKeyboardButton(text=gift, callback_data=f"book_{gift}")])

    if not buttons:
        await callback.message.answer("Все подарки уже забронированы 😢")
        return

    await callback.message.answer("Какой из подарков вы хотите забронировать?",
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


async def on_book(callback: CallbackQuery):
    gift_name = callback.data[5:]
    user_id = str(callback.from_user.id)
    full_name = callback.from_user.full_name

    bookings = await load_bookings()

    if user_already_chosen(callback.from_user.id, bookings):
        await callback.message.answer("Ты уже выбрал подарок)) Встретимся на празднике!))")
        return

    if bookings.get("bookings", {}).get(gift_name) is None:
        bookings["bookings"][gift_name] = full_name
        bookings["confirmed_users"].append(user_id)
        await save_bookings(bookings)

        await callback.message.answer(
            "Спасибо! Будем ждать тебя на дне рождения Амалии 09.08.2025 по ул. М. Гафури д. 46, "
            "в 14:00 - в центре развлечений Maza Park"
        )
    else:
        await callback.message.answer("Этот подарок уже забронирован кем-то другим 😢")


async def on_other_gift(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    bookings = await load_bookings()

    if user_already_chosen(callback.from_user.id, bookings):
        await callback.message.answer("Ты уже выбрал подарок)) Встретимся на празднике!))")
        return

    bookings["confirmed_users"].append(user_id)
    await save_bookings(bookings)

    await callback.message.answer(
        "Спасибо! Будем ждать тебя на дне рождения Амалии 09.08.2025 по ул. М. Гафури д. 46, "
        "в 14:00 - в центре развлечений Maza Park"
    )


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.message.register(on_start, CommandStart())
    dp.callback_query.register(on_view_list, F.data == "view_list")
    dp.callback_query.register(on_reserve, F.data == "reserve")
    dp.callback_query.register(on_other_gift, F.data == "other_gift")
    dp.callback_query.register(on_book, F.data.startswith("book_"))

    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
