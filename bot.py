import os
import asyncio
import logging
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8197564304  # <-- вставь свой ID

if not TOKEN:
    raise ValueError("BOT_TOKEN is missing")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

# 💥 ПРИВЕТСТВИЕ (НЕ ТРОГАЮ)
WELCOME = [
    "🔥 MUSIC ENGINE ONLINE",
    "🎧 Бот запущен — качай музыку",
    "⚡ Готов к взрыву треков",
    "🚀 Sound system activated"
]

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(WELCOME[0])

# ---------------- ADMIN PANEL ----------------
@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ нет доступа")

    await message.answer(
        "🛠 ADMIN PANEL\n\n"
        "/stats - users\n"
        "/ping - bot status\n"
        "/clear - clear cache"
    )

@dp.message(Command("stats"))
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"👥 users: {len(user_data)}")

@dp.message(Command("ping"))
async def ping(message: types.Message):
    await message.answer("🏓 alive")

@dp.message(Command("clear"))
async def clear(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_data.clear()
    await message.answer("🧹 cache cleared")

# ---------------- MUSIC API (STABLE) ----------------
def search_music(query: str):
    url = "https://itunes.apple.com/search"
    params = {
        "term": query,
        "limit": 5,
        "media": "music"
    }

    r = requests.get(url, params=params)
    data = r.json()

    results = []

    for item in data.get("results", []):
        if "previewUrl" in item:
            results.append({
                "name": item.get("trackName"),
                "artist": item.get("artistName"),
                "url": item.get("previewUrl")
            })

    return results

# ---------------- HANDLE ----------------
@dp.message()
async def handle(message: types.Message):
    text = message.text.strip()

    if text.startswith("http"):
        await message.answer("📥 видео пока без изменений")
        return

    await message.answer("🔎 ищу музыку...")

    results = search_music(text)

    if not results:
        await message.answer("❌ ничего не найдено")
        return

    user_data[message.from_user.id] = results

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🎵 {r['name']} - {r['artist']}",
            callback_data=f"play|{i}"
        )]
        for i, r in enumerate(results)
    ])

    await message.answer("🎧 выбери трек:", reply_markup=kb)

# ---------------- PLAY ----------------
@dp.callback_query(lambda c: c.data.startswith("play"))
async def play(callback: types.CallbackQuery):
    i = int(callback.data.split("|")[1])
    uid = callback.from_user.id

    results = user_data.get(uid, [])

    if i >= len(results):
        return await callback.message.answer("❌ ошибка выбора")

    track = results[i]

    await callback.message.answer_audio(
        audio=track["url"],
        title=track["name"],
        performer=track["artist"]
    )

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
