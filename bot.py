import os
import asyncio
import logging
import yt_dlp
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8197564304  # вставь свой ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

# 💥 БОМБИЧЕСКОЕ ПРИВЕТСТВИЕ
WELCOME_TEXTS = [
    "🔥 Добро пожаловать в MUSIC GOD BOT 🔥",
    "🎧 Тут музыка летает быстрее света",
    "💣 Включай треки — будет разнос",
    "🚀 Музыкальный портал активирован"
]

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(random.choice(WELCOME_TEXTS))

# ---------------- ADMIN PANEL ----------------
@dp.message(Command("admin"))
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("⛔ доступ закрыт")

    await message.answer(
        "🛠 ADMIN PANEL PRO\n\n"
        "/stats - пользователи\n"
        "/ping - бот жив?\n"
        "/clear - очистка кеша"
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
    await message.answer("🧹 кеш очищен")

# ---------------- MAIN ----------------
@dp.message()
async def handle(message: types.Message):
    text = message.text.strip()

    # 🎬 VIDEO
    if "http" in text:
        await message.answer("📥 качаю видео...")

        try:
            ydl_opts = {
                "format": "mp4",
                "outtmpl": "video.%(ext)s",
                "quiet": True,
                "socket_timeout": 10
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=True)
                file = ydl.prepare_filename(info)

            await message.answer_video(types.FSInputFile(file))

        except:
            await message.answer("❌ ошибка видео")
        return

    # 🎧 MUSIC SEARCH (ФИКС ДУБЛЕЙ)
    await message.answer("🔎 ищу музыку...")

    try:
        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "socket_timeout": 8,
            "extract_flat": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{text}", download=False)

        entries = info.get("entries", [])

        # ❌ УБИРАЕМ ДУБЛИКАТЫ
        seen = set()
        results = []
        for e in entries:
            if not e:
                continue
            title = e.get("title")
            if title and title not in seen:
                seen.add(title)
                results.append(e)

        results = results[:5]

        if not results:
            await message.answer("❌ ничего не найдено")
            return

        user_data[message.from_user.id] = results

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=r["title"][:40],
                callback_data=f"sel|{i}"
            )]
            for i, r in enumerate(results)
        ])

        await message.answer("🎧 выбери трек:", reply_markup=kb)

    except Exception as e:
        logging.error(e)
        await message.answer("❌ ошибка поиска")

# ---------------- SELECT ----------------
@dp.callback_query(lambda c: c.data.startswith("sel"))
async def select(callback: types.CallbackQuery):
    try:
        i = int(callback.data.split("|")[1])
        uid = callback.from_user.id

        results = user_data.get(uid, [])

        if i >= len(results):
            return await callback.message.answer("❌ ошибка выбора")

        url = results[i]["url"]

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="⬇️ скачать",
                callback_data=f"dl|{url}"
            )]
        ])

        await callback.message.answer("готово 👇", reply_markup=kb)

    except:
        await callback.message.answer("❌ ошибка")

# ---------------- DOWNLOAD ----------------
@dp.callback_query(lambda c: c.data.startswith("dl"))
async def download(callback: types.CallbackQuery):
    url = callback.data.split("|")[1]

    file_path = "music.mp3"

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path,
            "quiet": True,
            "socket_timeout": 10
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        await callback.message.answer_audio(types.FSInputFile(file_path))

    except:
        await callback.message.answer("❌ ошибка загрузки")

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
