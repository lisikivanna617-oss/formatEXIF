import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from PIL import Image
from PIL.ExifTags import TAGS

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "🔍 **EXIF METADATA EXTRACTOR**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✨ *Uncover hidden details behind any image.*\n\n"
        "📷 **What I can extract:**\n"
        "• Camera model & Lens details\n"
        "• Exposure settings (ISO, Shutter, Aperture)\n"
        "• Date, Time & GPS coordinates (if available)\n\n"
        "👉 *Just send any photo as a file (uncompressed) to inspect its EXIF data!*"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Send an Image", callback_data="help_exif")]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data == "help_exif")
async def callback_help(callback: CallbackQuery):
    await callback.answer("Send photo as a document or uncompressed image to read metadata!", show_alert=True)

@dp.message(F.photo | F.document)
async def extract_exif(message: Message):
    status_msg = await message.answer("🔄 **Downloading and reading EXIF data...**", parse_mode="Markdown")
    
    file_path = f"temp_{message.from_user.id}.jpg"
    
    try:
        # Визначаємо файл (фото чи документ)
        if message.photo:
            file_id = message.photo[-1].file_id
        else:
            if not message.document.mime_type or not message.document.mime_type.startswith('image/'):
                await status_msg.edit_text("❌ **Error:** Please send a valid image file.")
                return
            file_id = message.document.file_id
            
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=file_path)
        
        # Відкриваємо зображення через Pillow і дістаємо EXIF
        image = Image.open(file_path)
        exif_data = image.getexif()
        
        if not exif_data:
            await status_msg.edit_text("⚠️ **No EXIF data found** in this image (metadata might have been stripped).")
            if os.path.exists(file_path):
                os.remove(file_path)
            return
            
        exif_info = []
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            # Фільтруємо занадто великі бінарні дані
            if isinstance(value, bytes):
                try:
                    value = value.decode(errors='ignore')
                except:
                    value = "<binary data>"
            exif_info.append(f"• **{tag}**: `{value}`")
            
        # Форматуємо результат (обмежуємо довжину, щоб не перевищити ліміт Telegram)
        result_text = "📊 **EXIF METADATA REPORT**\n━━━━━━━━━━━━━━━━━━━\n" + "\n".join(exif_info[:25])
        
        done_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Analyze another", callback_data="help_exif")]
        ])
        
        await status_msg.edit_text(result_text, reply_markup=done_keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"EXIF Error: {e}")
        await status_msg.edit_text("❌ **Error:** Could not process image metadata.")
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("EXIF Bot is online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
