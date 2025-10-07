from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if BOT_TOKEN is None:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

user_data = {}

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    user_data[msg.from_user.id] = {}
    await msg.answer("Привет! 💸 Введи часовую ставку (₽/час):")

@dp.message_handler(lambda m: m.from_user.id in user_data and 'hourly_rate' not in user_data[m.from_user.id])
async def hourly_rate(msg: types.Message):
    try:
        user_data[msg.from_user.id]['hourly_rate'] = float(msg.text)
    except ValueError:
        await msg.answer("Пожалуйста, введи число.")
        return
    await msg.answer("Сколько оплата за один заказ (₽)?")

@dp.message_handler(lambda m: 'order_rate' not in user_data.get(m.from_user.id, {}))
async def order_rate(msg: types.Message):
    try:
        user_data[msg.from_user.id]['order_rate'] = float(msg.text)
    except ValueError:
        await msg.answer("Пожалуйста, введи число.")
        return
    await msg.answer("Сколько часов ты отработал сегодня?")

@dp.message_handler(lambda m: 'hours' not in user_data.get(m.from_user.id, {}))
async def hours(msg: types.Message):
    try:
        user_data[msg.from_user.id]['hours'] = float(msg.text)
    except ValueError:
        await msg.answer("Пожалуйста, введи число.")
        return
    await msg.answer("Сколько заказов ты доставил сегодня?")

@dp.message_handler(lambda m: 'orders' not in user_data.get(m.from_user.id, {}))
async def orders(msg: types.Message):
    try:
        user_data[msg.from_user.id]['orders'] = int(msg.text)
    except ValueError:
        await msg.answer("Пожалуйста, введи целое число.")
        return
    await msg.answer("Сколько из них с надбавкой +10₽?")

@dp.message_handler(lambda m: 'plus10_orders' not in user_data.get(m.from_user.id, {}))
async def plus10_orders(msg: types.Message):
    try:
        user_data[msg.from_user.id]['plus10_orders'] = int(msg.text)
    except ValueError:
        await msg.answer("Целое число, пожалуйста.")
        return
    await msg.answer("Сколько из них с надбавкой +30₽?")

@dp.message_handler(lambda m: 'plus30_orders' not in user_data.get(m.from_user.id, {}))
async def plus30_orders(msg: types.Message):
    try:
        user_data[msg.from_user.id]['plus30_orders'] = int(msg.text)
    except ValueError:
        await msg.answer("Целое число.")
        return
    await msg.answer("Сколько из них с надбавкой +70₽?")

@dp.message_handler(lambda m: 'plus70_orders' not in user_data.get(m.from_user.id, {}))
async def plus70_orders(msg: types.Message):
    try:
        user_data[msg.from_user.id]['plus70_orders'] = int(msg.text)
    except ValueError:
        await msg.answer("Целое число.")
        return
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Да", "Нет")
    await msg.answer("Была ли надбавка +10₽ к каждому заказу?", reply_markup=keyboard)

@dp.message_handler(lambda m: 'plus10_all' not in user_data.get(m.from_user.id, {}))
async def plus10_all(msg: types.Message):
    text = msg.text.lower()
    if text not in ("да", "нет"):
        await msg.answer("Ответь Да или Нет.")
        return
    user_data[msg.from_user.id]['plus10_all'] = (text == "да")
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Да", "Нет")
    await msg.answer("Была ли надбавка +15₽ к часовой ставке за погоду?", reply_markup=keyboard)

@dp.message_handler(lambda m: 'plus15_weather' not in user_data.get(m.from_user.id, {}))
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

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
