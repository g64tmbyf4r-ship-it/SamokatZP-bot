from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import asyncio
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_data = {}


@dp.message(Command("start"))
async def start(msg: types.Message):
    user_data[msg.from_user.id] = {"step": "hourly_rate"}
    await msg.answer("Привет! 💸 Введи часовую ставку (₽/час):")


@dp.message(F.text)
async def process(msg: types.Message):
    user_id = msg.from_user.id
    if user_id not in user_data:
        await msg.answer("Напиши /start, чтобы начать заново.")
        return

    step = user_data[user_id].get("step")

    # Шаг 1 — часовая ставка
    if step == "hourly_rate":
        try:
            user_data[user_id]["hourly_rate"] = float(msg.text)
            user_data[user_id]["step"] = "order_rate"
            await msg.answer("Сколько оплата за один заказ (₽)?")
        except ValueError:
            await msg.answer("Введи число, например 250.")
        return

    # Шаг 2 — ставка за заказ
    if step == "order_rate":
        try:
            user_data[user_id]["order_rate"] = float(msg.text)
            user_data[user_id]["step"] = "hours"
            await msg.answer("Сколько часов ты отработал сегодня?")
        except ValueError:
            await msg.answer("Введи число, например 5.")
        return

    # Шаг 3 — часы
    if step == "hours":
        try:
            user_data[user_id]["hours"] = float(msg.text)
            user_data[user_id]["step"] = "orders"
            await msg.answer("Сколько заказов ты доставил сегодня?")
        except ValueError:
            await msg.answer("Число, пожалуйста.")
        return

    # Шаг 4 — количество заказов
    if step == "orders":
        try:
            user_data[user_id]["orders"] = int(msg.text)
            user_data[user_id]["step"] = "plus10_orders"
            await msg.answer("Сколько из них с надбавкой +10₽?")
        except ValueError:
            await msg.answer("Целое число, пожалуйста.")
        return

    # Шаг 5 — +10₽ за заказы
    if step == "plus10_orders":
        try:
            user_data[user_id]["plus10_orders"] = int(msg.text)
            user_data[user_id]["step"] = "plus30_orders"
            await msg.answer("Сколько из них с надбавкой +30₽?")
        except ValueError:
            await msg.answer("Целое число.")
        return

    # Шаг 6 — +30₽ за заказы
    if step == "plus30_orders":
        try:
            user_data[user_id]["plus30_orders"] = int(msg.text)
            user_data[user_id]["step"] = "plus70_orders"
            await msg.answer("Сколько из них с надбавкой +70₽?")
        except ValueError:
            await msg.answer("Целое число.")
        return

    # Шаг 7 — +70₽
    if step == "plus70_orders":
        try:
            user_data[user_id]["plus70_orders"] = int(msg.text)
            user_data[user_id]["step"] = "plus10_all"
            kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("Да", "Нет")
            await msg.answer("Была ли надбавка +10₽ к каждому заказу?", reply_markup=kb)
        except ValueError:
            await msg.answer("Целое число.")
        return

    # Шаг 8 — надбавка ко всем заказам
    if step == "plus10_all":
        if msg.text.lower() not in ("да", "нет"):
            await msg.answer("Ответь 'Да' или 'Нет'.")
            return
        user_data[user_id]["plus10_all"] = (msg.text.lower() == "да")
        user_data[user_id]["step"] = "plus15_weather"
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("Да", "Нет")
        await msg.answer("Была ли надбавка +15₽ к часовой ставке за погоду?", reply_markup=kb)
        return

    # Шаг 9 — финальный расчёт
    if step == "plus15_weather":
        if msg.text.lower() not in ("да", "нет"):
            await msg.answer("Ответь 'Да' или 'Нет'.")
            return
        user_data[user_id]["plus15_weather"] = (msg.text.lower() == "да")

        data = user_data[user_id]
        base_salary = data['hours'] * data['hourly_rate'] + data['orders'] * data['order_rate']
        bonus_orders = (data['plus10_orders'] * 10 +
                        data['plus30_orders'] * 30 +
                        data['plus70_orders'] * 70)
        all_order_bonus = data['orders'] * 10 if data['plus10_all'] else 0
        weather_bonus = data['hours'] * 15 if data['plus15_weather'] else 0
        total = base_salary + bonus_orders + all_order_bonus + weather_bonus

        await msg.answer(
            f"💰 Расчёт за сегодня:\n"
            f"Часы: {data['hours']} × {data['hourly_rate']}₽ = {data['hours'] * data['hourly_rate']:.2f}₽\n"
            f"Заказы: {data['orders']} × {data['order_rate']}₽ = {data['orders'] * data['order_rate']:.2f}₽\n"
            f"Надбавки за заказы: {bonus_orders}₽\n"
            f"Надбавка +10₽ к каждому заказу: {all_order_bonus}₽\n"
            f"Надбавка за погоду: {weather_bonus}₽\n\n"
            f"💵 *ИТОГО: {total:.2f}₽*",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardRemove()
        )

        user_data.pop(user_id, None)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
