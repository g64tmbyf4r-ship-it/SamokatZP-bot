from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
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
    user_data[msg.from_user.id] = {}
    await msg.answer("Привет! 💸 Введи часовую ставку (₽/час):")

@dp.message(F.text.regexp(r"^\d+(\.\d+)?$") & (lambda msg: 'hourly_rate' not in user_data.get(msg.from_user.id, {})))
async def hourly_rate(msg: types.Message):
    user_data[msg.from_user.id]['hourly_rate'] = float(msg.text)
    await msg.answer("Сколько оплата за один заказ (₽)?")

@dp.message(lambda msg: 'order_rate' not in user_data.get(msg.from_user.id, {}))
async def order_rate(msg: types.Message):
    try:
        user_data[msg.from_user.id]['order_rate'] = float(msg.text)
    except ValueError:
        await msg.answer("Пожалуйста, введи число.")
        return
    await msg.answer("Сколько часов ты отработал сегодня?")

@dp.message(lambda msg: 'hours' not in user_data.get(msg.from_user.id, {}))
async def hours(msg: types.Message):
    try:
        user_data[msg.from_user.id]['hours'] = float(msg.text)
    except ValueError:
        await msg.answer("Пожалуйста, введи число.")
        return
    await msg.answer("Сколько заказов ты доставил сегодня?")

@dp.message(lambda msg: 'orders' not in user_data.get(msg.from_user.id, {}))
async def orders(msg: types.Message):
    try:
        user_data[msg.from_user.id]['orders'] = int(msg.text)
    except ValueError:
        await msg.answer("Пожалуйста, введи целое число.")
        return
    await msg.answer("Сколько из них с надбавкой +10₽?")

@dp.message(lambda msg: 'plus10_orders' not in user_data.get(msg.from_user.id, {}))
async def plus10_orders(msg: types.Message):
    try:
        user_data[msg.from_user.id]['plus10_orders'] = int(msg.text)
    except ValueError:
        await msg.answer("Целое число, пожалуйста.")
        return
    await msg.answer("Сколько из них с надбавкой +30₽?")

@dp.message(lambda msg: 'plus30_orders' not in user_data.get(msg.from_user.id, {}))
async def plus30_orders(msg: types.Message):
    try:
        user_data[msg.from_user.id]['plus30_orders'] = int(msg.text)
    except ValueError:
        await msg.answer("Целое число.")
        return
    await msg.answer("Сколько из них с надбавкой +70₽?")

@dp.message(lambda msg: 'plus70_orders' not in user_data.get(msg.from_user.id, {}))
async def plus70_orders(msg: types.Message):
    try:
        user_data[msg.from_user.id]['plus70_orders'] = int(msg.text)
    except ValueError:
        await msg.answer("Целое число.")
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Да", "Нет")
    await msg.answer("Была ли надбавка +10₽ к каждому заказу?", reply_markup=keyboard)

@dp.message(lambda msg: 'plus10_all' not in user_data.get(msg.from_user.id, {}))
async def plus10_all(msg: types.Message):
    text = msg.text.lower()
    if text not in ("да", "нет"):
        await msg.answer("Ответь Да или Нет.")
        return
    user_data[msg.from_user.id]['plus10_all'] = (text == "да")
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Да", "Нет")
    await msg.answer("Была ли надбавка +15₽ к часовой ставке за погоду?", reply_markup=keyboard)

@dp.message(lambda msg: 'plus15_weather' not in user_data.get(msg.from_user.id, {}))
async def plus15_weather(msg: types.Message):
    text = msg.text.lower()
    if text not in ("да", "нет"):
        await msg.answer("Ответь Да или Нет.")
        return
    user_data[msg.from_user.id]['plus15_weather'] = (text == "да")

    data = user_data[msg.from_user.id]
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

    user_data.pop(msg.from_user.id, None)


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
