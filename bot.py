import os
import asyncio
import logging
import random
import requests
import yt_dlp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8197564304

bot = Bot(token=TOKEN)
dp = Dispatcher()

cache = {}

# 💥 ЖИВОЕ ПРИВЕТСТВИЕ
WELCOME = [
    "🔥 MUSIC ENGINE ONLINE",
    "🎧 Бот запущен — качай музыку",
    "⚡ Готов к взрыву треков",
    "🚀 Sound system activated"
]

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(random.choice(WELCOME))

# ---------------- ADMIN ----------------
@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ нет доступа")

    await message.answer(
        "🛠 ADMIN PANEL PRO\n\n"
        "/stats - users\n"
        "/cache - кеш\n"
        "/clear - очистить\n"
        "/ping - проверка"
    )

@dp.message(Command("stats"))
async def stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"👥 users: {len(cache)}")

@dp.message(Command("cache"))
async def show_cache(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"🧠 cache size: {len(cache)}")

@dp.message(Command("clear"))
async def clear(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    cache.clear()
    await message.answer("🧹 cleared")

@dp.message(Command("ping"))
async def ping(message: types.Message):
    await message.answer("🏓 alive")

# ---------------- SOUND SEARCH (НОВЫЙ МЕТОД) ----------------
def soundcloud_search(query):
    url = f"https://m.soundcloud.com/search/sounds?q={query}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    
    if r.status_code != 200:
        return []

    # простой парсинг ссылок
    links = []
    for line in r.text.split("https://"):
        if "soundcloud.com" in line:
            link = "https://" + line.split('"')[0]
            if link not in links:
                links.append(link)

    return links[:5]

# ---------------- HANDLE ----------------
@dp.message()
async def handle(message: types.Message):
    text = message.text.strip()

    # 🎬 VIDEO
    if "http" in text:
        await message.answer("📥 скачиваю видео...")

        try:
            ydl_opts = {
                "format": "mp4",
                "outtmpl": "video.%(ext)s",
                "quiet": True
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                file = ydl.prepare_filename(info)

            await message.answer_video(types.FSInputFile(file))

        except Exception as e:
            logging.error(e)
            await message.answer("❌ ошибка видео")
        return

    # 🎧 MUSIC SEARCH (НОВЫЙ ENGINE)
    await message.answer("🔎 ищу музыку...")

    results = soundcloud_search(text)

    if not results:
        await message.answer("❌ ничего не найдено")
        return

    cache[message.from_user.id] = results

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎵 трек {i+1}", callback_data=f"play|{i}")]
        for i in range(len(results))
    ])

    await message.answer("🎧 выбери:", reply_markup=kb)

# ---------------- PLAY ----------------
@dp.callback_query(lambda c: c.data.startswith("play"))
async def play(callback: types.CallbackQuery):
    i = int(callback.data.split("|")[1])
    url = cache[callback.from_user.id][i]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ скачать", callback_data=f"dl|{url}")]
    ])

    await callback.message.answer("готово 👇", reply_markup=kb)

# ---------------- DOWNLOAD ----------------
@dp.callback_query(lambda c: c.data.startswith("dl"))
async def download(callback: types.CallbackQuery):
    url = callback.data.split("|")[1]

    file_path = "music.mp3"

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path,
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        await callback.message.answer_audio(types.FSInputFile(file_path))

    except Exception as e:
        logging.error(e)
        await callback.message.answer("❌ ошибка загрузки")

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
