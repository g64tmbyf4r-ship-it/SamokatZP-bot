import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram import F
from aiogram.fsm.storage.memory import MemoryStorage
from datetime import datetime
import asyncio
import json
import os

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 710958950  # твой Telegram ID
STATS_FILE = "stats.json"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === Работа со статистикой ===
def load_stats():
    """Загружает статистику из файла"""
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                data["unique_users"] = set(data["unique_users"])
                data["today_date"] = datetime.strptime(data["today_date"], "%Y-%m-%d").date()
                return data
            except Exception:
                pass
    return {"today_date": datetime.now().date(), "unique_users": set(), "calculations": 0}

def save_stats():
    """Сохраняет статистику в файл"""
    data = {
        "today_date": str(stats["today_date"]),
        "unique_users": list(stats["unique_users"]),
        "calculations": stats["calculations"],
    }
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

stats = load_stats()

def update_stats(user_id: int):
    """Обновляет статистику за день"""
    global stats
    today = datetime.now().date()
    if stats["today_date"] != today:
        stats = {"today_date": today, "unique_users": set(), "calculations": 0}
    stats["unique_users"].add(user_id)
    stats["calculations"] += 1
    save_stats()

# === Состояния ===
class Form(StatesGroup):
    hourly_rate = State()
    order_rate_15 = State()
    hours_worked = State()
    orders_15 = State()
    orders_30 = State()
    bonus_10 = State()
    bonus_30 = State()
    bonus_70 = State()
    weather_bonus_orders = State()
    weekend_bonus_hourly = State()

# === Логика ===
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer("Привет! 💸 Введи часовую ставку (₽/час):")
    await state.set_state(Form.hourly_rate)

@dp.message(Form.hourly_rate)
async def hourly_rate_handler(message: types.Message, state: FSMContext):
    await state.update_data(hourly_rate=float(message.text))
    await message.answer("📦 Какая у тебя оплата за заказ 15-минутный (₽):")
    await state.set_state(Form.order_rate_15)

@dp.message(Form.order_rate_15)
async def order_rate_handler(message: types.Message, state: FSMContext):
    await state.update_data(order_rate_15=float(message.text))
    await message.answer("⏰ Сколько часов отработано сегодня?")
    await state.set_state(Form.hours_worked)

@dp.message(Form.hours_worked)
async def hours_handler(message: types.Message, state: FSMContext):
    await state.update_data(hours=float(message.text))
    await message.answer("🚴‍♂️ Сколько 15-минутных заказов доставлено?")
    await state.set_state(Form.orders_15)

@dp.message(Form.orders_15)
async def orders15_handler(message: types.Message, state: FSMContext):
    await state.update_data(orders_15=int(message.text))
    await message.answer("🚚 Сколько 30-минутных заказов доставлено?")
    await state.set_state(Form.orders_30)

@dp.message(Form.orders_30)
async def orders30_handler(message: types.Message, state: FSMContext):
    await state.update_data(orders_30=int(message.text))
    await message.answer("🔹 Сколько заказов с надбавкой +10₽ за 45 доставленных заказов за день?")
    await state.set_state(Form.bonus_10)

@dp.message(Form.bonus_10)
async def bonus10_handler(message: types.Message, state: FSMContext):
    await state.update_data(bonus_10=int(message.text))
    await message.answer("🔸 Сколько заказов с надбавкой +30₽?")
    await state.set_state(Form.bonus_30)

@dp.message(Form.bonus_30)
async def bonus30_handler(message: types.Message, state: FSMContext):
    await state.update_data(bonus_30=int(message.text))
    await message.answer("🔺 Сколько заказов с надбавкой +70₽?")
    await state.set_state(Form.bonus_70)

@dp.message(Form.bonus_70)
async def bonus70_handler(message: types.Message, state: FSMContext):
    await state.update_data(bonus_70=int(message.text))
    await message.answer("📦 Была ли надбавка +10₽ к каждому заказу сегодня за погодные условия? (да/нет)")
    await state.set_state(Form.weather_bonus_orders)

@dp.message(Form.weather_bonus_orders)
async def weather_bonus_orders_handler(message: types.Message, state: FSMContext):
    await state.update_data(weather_bonus_orders=message.text.lower() == "да")
    await message.answer("🌦️ Была ли надбавка +15₽ к часовой ставке за вс/пн? (да/нет)")
    await state.set_state(Form.weekend_bonus_hourly)

@dp.message(Form.weekend_bonus_hourly)
async def weekend_bonus_handler(message: types.Message, state: FSMContext):
    data = await state.update_data(weekend_bonus_hourly=message.text.lower() == "да")

    hourly_rate = data["hourly_rate"]
    order_rate_15 = data["order_rate_15"]
    hours = data["hours"]
    orders_15 = data["orders_15"]
    orders_30 = data["orders_30"]
    bonus_10 = data["bonus_10"]
    bonus_30 = data["bonus_30"]
    bonus_70 = data["bonus_70"]
    weather_bonus_orders = data["weather_bonus_orders"]
    weekend_bonus_hourly = data["weekend_bonus_hourly"]

    # Расчёт
    hourly_total = hours * (hourly_rate + (15 if weekend_bonus_hourly else 0))
    orders_total = (orders_15 * order_rate_15) + (orders_30 * (order_rate_15 + 10))
    bonuses_total = (bonus_10 * 10) + (bonus_30 * 30) + (bonus_70 * 70)
    weather_bonus_total = (orders_15 + orders_30) * 10 if weather_bonus_orders else 0

    total = hourly_total + orders_total + bonuses_total + weather_bonus_total

    # Обновляем статистику
    update_stats(message.from_user.id)

    text = (
        f"📊 Итог за день:\n\n"
        f"⏰ Часы: {hours} × {hourly_rate}₽ = {hourly_total:.2f}₽\n"
        f"🚴 15-мин заказов: {orders_15} × {order_rate_15}₽ = {orders_15 * order_rate_15:.2f}₽\n"
        f"🚚 30-мин заказов: {orders_30} × {order_rate_15 + 10}₽ = {orders_30 * (order_rate_15 + 10):.2f}₽\n"
        f"💰 Надбавки: +{bonuses_total}₽\n"
        f"🌦️ Погодная надбавка: +{weather_bonus_total}₽\n\n"
        f"💸 ИТОГО: <b>{total:.2f}₽</b>"
    )

    await message.answer(text, parse_mode="HTML")
    await state.clear()

@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    """Показывает статистику (только для админа)"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа к статистике.")
        return

    today = datetime.now().strftime("%d.%m.%Y")
    total_users = len(stats["unique_users"])
    total_calculations = stats["calculations"]

    text = (
        f"📊 <b>Статистика за {today}</b>\n\n"
        f"👥 Уникальных пользователей: {total_users}\n"
        f"🧮 Всего расчётов за день: {total_calculations}\n"
        f"💾 Дата последнего сохранения: {stats['today_date']}"
    )

    await message.answer(text, parse_mode="HTML")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
