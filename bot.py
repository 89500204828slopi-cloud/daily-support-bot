import asyncio
import json
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

# ---------------------------------------------------------
# Настройки
# ---------------------------------------------------------

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "128055849"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATA_FILE = "wish_users.json"

# ---------------------------------------------------------
# Пожелания
# ---------------------------------------------------------

WISHES = [
    "Сегодня хороший день, чтобы позволить себе спокойствие.",
    "Пусть сегодняшнее утро начнётся мягко.",
    "Иногда достаточно одного шага, и этого уже достаточно.",
    "Внутри всегда больше сил, чем кажется.",
    "Этот день может принести что-то хорошее.",
    "Пусть сегодня будет немного света.",
    "Хорошие перемены приходят постепенно.",
    "Можно замедлиться и позволить себе передышку.",
    "Сегодня подойдёт для чего-то приятного.",
    "Пусть мысли становятся мягче, а сердце теплее.",
    "Путь продолжается, даже если шаги маленькие.",
    "Можно опереться на то, что уже есть.",
    "Пусть этот день будет чуть легче.",
    "Всё нужное уже рядом.",
    "Пусть сегодня получится найти что-то доброе."
]

# ---------------------------------------------------------
# Хранение данных
# ---------------------------------------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------
# Получить структуру пользователя
# ---------------------------------------------------------

def get_user(user_id: int):
    data = load_data()
    uid = str(user_id)

    if uid not in data:
        data[uid] = {
            "last_wish_date": None,
            "last_wish_text": None,
            "last_streak_date": None,
            "streak": 0,
            "total_wishes": 0
        }
        save_data(data)

    return data, data[uid]

# ---------------------------------------------------------
# Меню
# ---------------------------------------------------------

def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ Получить пожелание", callback_data="get_wish")]
        ]
    )

# ---------------------------------------------------------
# Команда /start
# ---------------------------------------------------------

@dp.message(Command("start"))
async def start_cmd(message):
    await message.answer(
        "✨ Добро пожаловать!\n\n"
        "Каждый день здесь можно получить тёплое пожелание.\n"
        "Нажми кнопку ниже:",
        reply_markup=main_menu()
    )

# ---------------------------------------------------------
# Логика получения пожелания
# ---------------------------------------------------------

@dp.callback_query(lambda q: q.data == "get_wish")
async def process_get_wish(query: CallbackQuery):
    user_id = query.from_user.id
    now = datetime.now().date()

    data, user = get_user(user_id)

    # Особый режим — владелец без ограничений
    ignore_limit = user_id == OWNER_ID

    # ✨ Если уже есть пожелание на сегодня
    if not ignore_limit and user["last_wish_date"] == now.isoformat():
        wish = user["last_wish_text"]

        await query.message.answer(
            f"Пожелание на сегодня уже получено:\n\n"
            f"«{wish}»\n\n"
            f"Возвращайся завтра 💛",
            reply_markup=main_menu()
        )
        return

    # ✨ Выдаём новое пожелание
    import random
    wish = random.choice(WISHES)

    # Обновление общей статистики
    user["last_wish_date"] = now.isoformat()
    user["last_wish_text"] = wish
    user["total_wishes"] += 1

    # Стрик
    if user["last_streak_date"] is not None:
        last_date = datetime.fromisoformat(user["last_streak_date"]).date()
        if (now - last_date).days == 1:
            user["streak"] += 1
        else:
            user["streak"] = 1
    else:
        user["streak"] = 1

    user["last_streak_date"] = now.isoformat()

    save_data(data)

    # Ответ пользователю
    await query.message.answer(
        f"«{wish}»\n\n"
        f"🔥 Стрик: {user['streak']} дней подряд\n"
        f"📊 Всего пожеланий: {user['total_wishes']}",
        reply_markup=main_menu()
    )

# ---------------------------------------------------------
# Старт
# ---------------------------------------------------------

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


