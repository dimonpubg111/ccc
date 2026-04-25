import os
import asyncio
import logging
import yt_dlp

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8197564304  # <-- вставь свой ID

if not TOKEN:
    raise ValueError("BOT_TOKEN missing")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_cache = {}

# 💥 РУССКИЕ ПРИВЕТСТВИЯ (как ты хотел)
WELCOME = [
    "🔥 Привет! Я MUSIC BOT — качай любые треки",
    "🎧 Добро пожаловать! Сейчас найдём тебе музыку",
    "⚡ Готов к взрыву музыки",
    "🚀 Включай звук — поехали"
]

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(WELCOME[0])

# ---------------- ADMIN ----------------
@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ нет доступа")

    await message.answer(
        "🛠 АДМИН ПАНЕЛЬ\n\n"
        "/stats - пользователи\n"
        "/cache - посмотреть кеш\n"
        "/clear - очистить кеш\n"
        "/ping - проверка"
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
    await message.answer(f"🧠 кеш: {len(user_cache)} пользователей")

@dp.message(Command("clear"))
async def clear(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    user_cache.clear()
    await message.answer("🧹 кеш очищен")

@dp.message(Command("ping"))
async def ping(message: types.Message):
    await message.answer("🏓 бот работает")

# ---------------- MUSIC SEARCH ----------------
@dp.message()
async def handle(message: types.Message):
    text = message.text.strip()

    if "http" in text:
        await message.answer("📥 скачиваю видео/аудио...")

        try:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "music.%(ext)s",
                "quiet": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192"
                }]
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                file = ydl.prepare_filename(info).replace(".webm", ".mp3")

            await message.answer_audio(types.FSInputFile(file))

        except Exception as e:
            logging.error(e)
            await message.answer("❌ ошибка скачивания")

        return

    await message.answer("🔎 ищу музыку...")

    try:
        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "format": "bestaudio"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{text}", download=False)

        results = info.get("entries", [])

        if not results:
            await message.answer("❌ ничего не найдено")
            return

        user_cache[message.from_user.id] = results

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=r["title"][:40],
                callback_data=f"play|{i}"
            )]
            for i, r in enumerate(results)
        ])

        await message.answer("🎧 выбери трек:", reply_markup=kb)

    except Exception as e:
        logging.error(e)
        await message.answer("❌ ошибка поиска")

# ---------------- PLAY ----------------
@dp.callback_query(lambda c: c.data.startswith("play"))
async def play(callback: types.CallbackQuery):
    i = int(callback.data.split("|")[1])
    uid = callback.from_user.id

    results = user_cache.get(uid, [])

    if i >= len(results):
        return await callback.message.answer("❌ ошибка выбора")

    url = results[i]["webpage_url"]

    await callback.message.answer("⬇️ скачиваю трек...")

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "music.%(ext)s",
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info).replace(".webm", ".mp3")

        await callback.message.answer_audio(types.FSInputFile(file))

    except Exception as e:
        logging.error(e)
        await callback.message.answer("❌ ошибка загрузки")

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
