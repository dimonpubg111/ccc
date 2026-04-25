import asyncio
import os
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8570431888:AAEQY3Rwo8ElORJSShUzl6VesysFEkz7yyU"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ---------------- START ----------------
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎵 Отправь название песни или ссылку TikTok"
    )

# ---------------- TIKTOK / LINK ----------------
@dp.message(lambda m: m.text and "http" in m.text)
async def handle_link(message: Message):
    url = message.text

    await message.answer("📥 Загружаю...")

    ydl_opts = {
        "outtmpl": "video.%(ext)s",
        "format": "mp4",
        "quiet": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info)

        await message.answer_video(types.FSInputFile(file))

        # кнопка скачать музыку
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎧 Скачать музыку", callback_data=f"music|{url}")]
        ])

        await message.answer("Что дальше?", reply_markup=kb)

    except:
        await message.answer("❌ Не удалось скачать видео")

# ---------------- MUSIC MENU ----------------
@dp.callback_query(lambda c: c.data.startswith("music"))
async def music_menu(callback: types.CallbackQuery):
    url = callback.data.split("|")[1]

    await callback.message.answer("🔎 Ищу аудио...")

    ydl_opts = {
        "quiet": True,
        "format": "bestaudio"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get("title")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬇️ Скачать аудио", callback_data=f"dl|{url}")]
    ])

    await callback.message.answer(f"🎵 {title}", reply_markup=kb)

# ---------------- DOWNLOAD AUDIO ----------------
@dp.callback_query(lambda c: c.data.startswith("dl"))
async def download_audio(callback: types.CallbackQuery):
    url = callback.data.split("|")[1]

    file_path = "music.mp3"

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": file_path,
        "quiet": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        await callback.message.answer_audio(types.FSInputFile(file_path))

    except:
        await callback.message.answer("❌ Ошибка загрузки")

# ---------------- SEARCH MUSIC ----------------
@dp.message()
async def search_music(message: Message):
    query = message.text

    await message.answer("🔎 Ищу треки...")

    ydl_opts = {
        "quiet": True,
        "noplaylist": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)

    results = info["entries"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=r["title"][:40],
            callback_data=f"dl|{r['webpage_url']}"
        )]
        for r in results
    ])

    await message.answer("🎧 Выбери трек:", reply_markup=kb)

# ---------------- RUN ----------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
