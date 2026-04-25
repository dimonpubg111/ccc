import os
import random
import requests

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8197564304

bot = Bot(token=TOKEN)
dp = Dispatcher()

cache = {}

# 💥 СПОТИФАЙ-СТИЛЬ
WELCOME = """
🎧 SPOTIFY MODE

🔥 Введи название трека
🎵 Я найду музыку из лучших источников
⚡ Быстро и стабильно
"""

# ---------------- SEARCH ENGINE (2 API fallback) ----------------
def search_music(query):
    results = []

    # 1️⃣ Deezer
    try:
        r = requests.get("https://api.deezer.com/search", params={"q": query}).json()

        for item in r.get("data", [])[:3]:
            if item.get("preview"):
                results.append({
                    "title": item["title"],
                    "artist": item["artist"]["name"],
                    "audio": item["preview"]
                })
    except:
        pass

    # 2️⃣ iTunes fallback (если Deezer пустой)
    if not results:
        try:
            r = requests.get(
                "https://itunes.apple.com/search",
                params={"term": query, "limit": 3, "media": "music"}
            ).json()

            for item in r.get("results", []):
                if item.get("previewUrl"):
                    results.append({
                        "title": item["trackName"],
                        "artist": item["artistName"],
                        "audio": item["previewUrl"]
                    })
        except:
            pass

    return results

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(WELCOME)

# ---------------- HANDLE ----------------
@dp.message()
async def handle(message: types.Message):
    text = message.text.strip()

    if text.startswith("http"):
        await message.answer("📥 ссылка пока не в Spotify режиме")
        return

    await message.answer("🔎 Spotify ищет музыку...")

    results = search_music(text)

    if not results:
        await message.answer("❌ ничего не найдено")
        return

    cache[message.from_user.id] = results

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🎵 {r['title']} — {r['artist']}",
            callback_data=f"play|{i}"
        )]
        for i, r in enumerate(results)
    ])

    kb.inline_keyboard.append([
        InlineKeyboardButton(text="🔄 ещё", callback_data="more")
    ])

    await message.answer("🎧 Spotify Results:", reply_markup=kb)

# ---------------- PLAY ----------------
@dp.callback_query(lambda c: c.data.startswith("play"))
async def play(callback: types.CallbackQuery):
    i = int(callback.data.split("|")[1])

    data = cache.get(callback.from_user.id, [])

    if i >= len(data):
        return await callback.message.answer("❌ ошибка выбора")

    track = data[i]

    await callback.message.answer_audio(
        audio=track["audio"],
        title=track["title"],
        performer=track["artist"]
    )

# ---------------- MORE ----------------
@dp.callback_query(lambda c: c.data == "more")
async def more(callback: types.CallbackQuery):
    await callback.message.answer("🔎 просто введи новый запрос")

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
