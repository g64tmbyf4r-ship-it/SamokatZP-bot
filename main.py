import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio
import os

# Включаем логи для отладки
logging.basicConfig(level=logging.INFO)

# Получаем токен из переменных окружения (Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище данных пользователей
user_data = {}


@dp.message(Command("start"))
async def start(msg: types.Message):
    user_data[msg.from_user.id] = {}
    user_data[msg.from_user.id]["step"] = "hourly_rate"
    await msg.answer("Привет! 💸 Введи часовую ставку (₽/час):")


@dp.message(F.text)
async def process(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text.strip()

    # Если пользователь не начинал с /start
    if user_id not in user_data or "step" not in user_data[user_id]:
        user_data[user_id] = {"step": "hourly_rate"}
        await msg.answer("Начнём заново. 💸 Введи часовую ставку (₽/час):")
        return

    step = user_data[user_id]["step"]

    # === ЛОГИКА ВОПРОСОВ ===

    if step == "hourly_rate":
        try:
            user_data[user_id]["hourly_rate"] = float(text)
            user_data[user_id]["step"] = "order_rate"
            await msg.answer("💰 Сколько оплата за один заказ (₽)?")
        except ValueError:
            await msg.answer("❌ Введи число, например: 250")
            return

    elif step == "order_rate":
        try:
            user_data[user_id]["order_rate"] = float(text)
            user_data[user_id]["step"] = "hours"
            await msg.answer("⏰ Сколько часов ты отработал сегодня?")
        except ValueError:
            await msg.answer("❌ Введи число, например: 8")
            return

    elif step == "hours":
        try:
            user_data[user_id]["hours"] = float(text)
            user_data[user_id]["step"] = "orders"
            await msg.answer("📦 Сколько заказов доставил сегодня?")
        except ValueError:
            await msg.answer("❌ Введи число, например: 15")
            return

    elif step == "orders":
        try:
            user_data[user_id]["orders"] = int(text)
            user_data[user_id]["step"] = "bonus10"
            await msg.answer("➕ Сколько заказов с надбавкой +10₽?")
        except ValueError:
            await msg.answer("❌ Введи число, например: 3")
            return

    elif step == "bonus10":
        try:
            user_data[user_id]["bonus10"] = int(text)
            user_data[user_id]["step"] = "bonus30"
            await msg.answer("🚀 Сколько заказов с надбавкой +30₽?")
        except ValueError:
            await msg.answer("❌ Введи число, например: 2")
            return

    elif step == "bonus30":
        try:
            user_data[user_id]["bonus30"] = int(text)
            user_data[user_id]["step"] = "bonus70"
            await msg.answer("🔥 Сколько заказов с надбавкой +70₽?")
        except ValueError:
            await msg.answer("❌ Введи число, например: 1")
            return

    elif step == "bonus70":
        try:
            user_data[user_id]["bonus70"] = int(text)
            user_data[user_id]["step"] = "global10"
            await msg.answer("📦 Была ли надбавка +10₽ к каждому заказу сегодня? (да/нет)")
        except ValueError:
            await msg.answer("❌ Введи число, например: 0")
            return

    elif step == "global10":
        answer = text.lower()
        user_data[user_id]["global10"] = (answer == "да")
        user_data[user_id]["step"] = "weather15"
        await msg.answer("🌦️ Была ли надбавка +15₽ к часовой ставке за погоду? (да/нет)")

    elif step == "weather15":
        answer = text.lower()
        user_data[user_id]["weather15"] = (answer == "да")

        # === РАСЧЁТ ===
        data = user_data[user_id]

        hourly_rate = data["hourly_rate"]
        if data["weather15"]:
            hourly_rate += 15

        base = data["hours"] * hourly_rate
        order_total = data["orders"] * data["order_rate"]

        # Надбавки
        bonus_total = (
            data["bonus10"] * 10
            + data["bonus30"] * 30
            + data["bonus70"] * 70
        )

        if data["global10"]:
            bonus_total += data["orders"] * 10

        total = base + order_total + bonus_total

        await msg.answer(
            f"💵 <b>Итог за сегодня:</b>\n"
            f"— Часов: {data['hours']} × {hourly_rate}₽ = {base:.0f}₽\n"
            f"— Заказы: {data['orders']} × {data['order_rate']}₽ = {order_total:.0f}₽\n"
            f"— Надбавки: {bonus_total:.0f}₽\n\n"
            f"💰 <b>Всего:</b> {total:.0f}₽",
            parse_mode="HTML"
        )

        # После вывода сбрасываем шаг
        user_data[user_id]["step"] = "done"


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
