import os
import yt_dlp
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties

# قراءة التوكن من متغير البيئة
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("يرجى إضافة متغير TOKEN في إعدادات البيئة.")
else:
    print("تم تحميل التوكن بنجاح:", TOKEN)  # طباعة التوكن للتأكد

# حذف الـ webhook الحالي
def delete_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/deleteWebhook"
    response = requests.get(url)
    print("Delete Webhook Response:", response.text)

# إعداد البوت
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# لتخزين روابط المستخدمين والجودات المختارة
user_video_links = {}

# تحميل الفيديو بالجودة المختارة
def download_video(url, quality):
    options = {
        'format': quality,
        'outtmpl': '%(title)s.%(ext)s'
    }
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# الحصول على الجودات المتاحة
def get_available_formats(url):
    with yt_dlp.YoutubeDL() as ydl:
        info = ydl.extract_info(url, download=False)
        formats = info.get('formats', [])
        available_formats = []
        labels_seen = set()

        for f in formats:
            height = f.get('height')
            acodec = f.get('acodec')
            vcodec = f.get('vcodec')

            if acodec != 'none' and acodec and vcodec != 'none' and vcodec and height:
                label = f"{height}p"
                if label not in labels_seen:
                    available_formats.append((f.get('format_id'), label))
                    labels_seen.add(label)

        def sort_key(item):
            return int(item[1].replace("p", ""))

        return sorted(available_formats, key=sort_key, reverse=True)

# بدء المحادثة
@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("أرسل رابط فيديو من يوتيوب أو فيسبوك لتحميله.")

# استقبال الروابط
@router.message()
async def video_handler(message: Message):
    url = message.text.strip()
    if any(x in url for x in ["youtube.com", "youtu.be", "facebook.com"]):
        await message.answer("جاري تحليل الرابط للحصول على الجودات المتوفرة...")

        try:
            available_formats = get_available_formats(url)
            if not available_formats:
                await message.answer("لم يتم العثور على جودات متاحة.")
                return

            buttons = [[types.KeyboardButton(text=label)] for _, label in available_formats]
            keyboard = types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

            user_video_links[message.from_user.id] = {
                "url": url,
                "formats": {label: fmt for fmt, label in available_formats}
            }

            await message.answer("اختر الجودة التي تريد تحميل الفيديو بها:", reply_markup=keyboard)

        except Exception as e:
            await message.answer(f"حدث خطأ أثناء جلب الجودات: {e}")
    elif message.from_user.id in user_video_links:
        user_data = user_video_links[message.from_user.id]
        chosen_label = message.text.strip()
        format_id = user_data["formats"].get(chosen_label)

        if not format_id:
            await message.answer("الجودة التي اخترتها غير صحيحة.")
            return

        await message.answer("جاري تحميل الفيديو بالجودة المحددة...")

        try:
            file_path = download_video(user_data["url"], format_id)
            await message.answer_document(types.FSInputFile(file_path))
            os.remove(file_path)
            await message.answer("تم تحميل الفيديو بنجاح.", reply_markup=types.ReplyKeyboardRemove())
            user_video_links.pop(message.from_user.id)
        except Exception as e:
            await message.answer(f"حدث خطأ أثناء تحميل الفيديو: {e}")
    else:
        await message.answer("يرجى إرسال رابط فيديو أولاً.")

# تشغيل البوت
async def main():
    delete_webhook()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
