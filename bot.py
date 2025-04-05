import os
import yt_dlp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from aiogram.filters import CommandStart

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("يرجى إضافة متغير TOKEN في إعدادات البيئة.")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

@router.message(CommandStart())
async def start(message: types.Message):
    await message.answer("أرسل رابط يوتيوب لتحميل الفيديو.")

@router.message()
async def handle_video(message: types.Message):
    url = message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await message.answer("الرجاء إرسال رابط يوتيوب فقط.")
        return

    await message.answer("جاري تحميل الفيديو، انتظر قليلاً...")

    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': 'video.%(ext)s'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        await message.answer_document(types.FSInputFile(file_path))
        os.remove(file_path)

    except Exception as e:
        await message.answer(f"حدث خطأ أثناء التحميل:\n{str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
