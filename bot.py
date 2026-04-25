import os
import requests
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8197564304  # твой ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_cache = {}

# 💥 ПРИВЕТСТВИЕ (как ты хотел — простое и живое)
WELCOME = [
    "🔥 Привет! Я MUSIC BOT",
    "🎧 Готов найти любую музыку",
    "⚡ Введи название трека",
    "🚀 Музыка уже ждёт тебя"
]

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(random.choice(WELCOME))

# ---------------- ADMIN PANEL ----------------
@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ нет доступа")

    await message.answer(
        "🛠 ADMIN PANEL\n\n"
        "/stats - users\n"
        "/cache - показать кеш\n"
        "/clear - очистить кеш\n"
        "/ping - статус"
    )

@dp.message(Command("stats"))
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"👥 users: {len(user_cache)}")

@dp.message(Command("cache"))
async def cache(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"🧠 кеш записей: {len(user_cache)}")

@dp.message(Command("clear"))
async def clear(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_cache.clear()
    await message.answer("🧹 кеш очищен")

@dp.message(Command("ping"))
async def ping(message: types.Message):
    await message.answer("🏓 bot alive")

# ---------------- MUSIC API (STABLE ENGINE) ----------------
def search_music(query: str):
    url = "https://api.deezer.com/search"
    r = requests.get(url, params={"q": query})
    data = r.json()

    results = []

    for item in data.get("data", [])[:5]:
        results.append({
            "title": item["title"],
            "artist": item["artist"]["name"],
            "preview": item["preview"]
        })

    return results

# ---------------- HANDLE ----------------
@dp.message()
async def handle(message: types.Message):
    text = message.text.strip()

    if text.startswith("http"):
        await message.answer("📥 видео режим пока отдельно")
        return

    await message.answer("🔎 ищу музыку...")

    results = search_music(text)

    if not results:
        await message.answer("❌ ничего не найдено")
        return

    user_cache[message.from_user.id] = results

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🎵 {r['title']} - {r['artist']}",
            callback_data=f"play|{i}"
        )]
        for i, r in enumerate(results)
    ])

    await message.answer("🎧 выбери трек:", reply_markup=kb)

# ---------------- PLAY ----------------
@dp.callback_query(lambda c: c.data.startswith("play"))
async def play(callback: types.CallbackQuery):
    i = int(callback.data.split("|")[1])
    data = user_cache.get(callback.from_user.id, [])

    if i >= len(data):
        return await callback.message.answer("❌ ошибка выбора")

    track = data[i]

    await callback.message.answer_audio(
        audio=track["preview"],
        title=track["title"],
        performer=track["artist"]
    )

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
