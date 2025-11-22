import asyncio
import json
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "128055849"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DATA_FILE = "wish_users.json"

# ---------------------------------------------------------
# Пожелания (гендерно-нейтральные)
# ---------------------------------------------------------
WISHES = [
    "Сегодня хороший день, чтобы позволить себе быть собой.",
    "Пусть сегодняшний день подарит спокойствие и ясность.",
    "Иногда самое важное — просто сделать маленький шаг.",
    "Сил достаточно, даже если кажется иначе.",
    "Хорошие перемены могут начинаться незаметно.",
    "Всё складывается лучше, чем кажется на первый взгляд.",
    "Пусть этот день принесёт немного света.",
    "Внутри больше ресурсов, чем кажется.",
    "Сегодня идеально подходит для чего-то приятного.",
    "Путь всегда продолжается, даже если шаги маленькие.",
    "Пусть мысли становятся мягче, а сердце теплее.",
    "Можно замедлиться и позволить себе отдохнуть.",
    "Этот день подойдёт для чего-то доброго.",
    "Всё нужное уже рядом.",
    "Пусть сегодняшнее утро начнётся спокойно.",
]

# ---------------------------------------------------------
# Работа с файлом данных
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
# Проверка: можно ли получить пожелание сегодня?
# Логика: 1 раз в сутки, сброс в полночь
# ---------------------------------------------------------
def can_get_today_wish(user_data, now):
    """
    Возвращает:
    - True, None — если можно получить новое пожелание
    - False, remaining_timedelta — если уже было сегодня
    """
    last_time = user_data.get("last_wish_time")

    # Если пожеланий ещё не было — можно
    if not last_time:
        return True, None

    last_dt = datetime.fromisoformat(last_time)

    # Если дата последнего пожелания меньше сегодняшней — можно
    if last_dt.date() < now.date():
        return True, None

    # Иначе — нет, считаем время до полуночи
    tomorrow = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
    remaining = tomorrow - now
    return False, remaining


# ---------------------------------------------------------
# Кнопка “Получить пожелание”
# ---------------------------------------------------------
def main_menu():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Получить пожелание ✨", callback_data="get_wish")]
    ])
    return kb


# ---------------------------------------------------------
# Команда /start
# ---------------------------------------------------------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "✨ Добро пожаловать!\n"
        "Каждый день здесь можно получить тёплое пожелание.\n\n"
        "Нажми кнопку ниже:",
        reply_markup=main_menu()
    )


# ---------------------------------------------------------
# Обработка кнопки “Получить пожелание”
# ---------------------------------------------------------
@dp.callback_query(lambda q: q.data == "get_wish")
async def give_wish(query: types.CallbackQuery):
    user_id = str(query.from_user.id)
    now = datetime.now()

    data = load_data()
    user_data = data.get(user_id, {})

    # Особый режим — владелец без кулдауна
    if query.from_user.id == OWNER_ID:
        can_get = True
        remaining = None
    else:
        can_get, remaining = can_get_today_wish(user_data, now)

    # Если пожелание можно получить — выдаём новое
    if can_get:
        wish = WISHES[now.day % len(WISHES)]

        # Записываем информацию
        user_data["last_wish_time"] = now.isoformat()
        user_data["last_wish"] = wish

        # стрик
        last_time = user_data.get("last_wish_time_prev")
        if last_time:
            last_dt = datetime.fromisoformat(last_time)
            # если вчера — +1 стрик
            if last_dt.date() == (now.date() - timedelta(days=1)):
                user_data["streak"] = user_data.get("streak", 0) + 1
            else:
                user_data["streak"] = 1
        else:
            user_data["streak"] = 1

        user_data["last_wish_time_prev"] = user_data["last_wish_time"]

        # общее количество
        user_data["total"] = user_data.get("total", 0) + 1

        data[user_id] = user_data
        save_data(data)

        await query.message.answer(
            f"✨ Пожелание:\n\n"
            f"«{wish}»\n\n"
            f"🔥 Стрик: {user_data['streak']} дней подряд\n"
            f"📊 Всего пожеланий: {user_data['total']}"
        )
        return

    # Если уже получал сегодня → показываем старое
    old_wish = user_data.get("last_wish", "Пожелание отсутствует.")

    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60

    await query.message.answer(
        "Пожелание на сегодня уже получено.\n\n"
        "Сегодняшнее пожелание:\n\n"
        f"«{old_wish}»\n\n"
        f"🔥 Стрик: {user_data.get('streak', 0)} дней подряд\n"
        f"📊 Всего пожеланий: {user_data.get('total', 0)}\n\n"
        f"Следующее будет доступно через {hours} ч {minutes} мин."
    )


# ---------------------------------------------------------
# Старт бота
# ---------------------------------------------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
