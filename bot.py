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
        "🔍 **IMAGE INSPECTOR ENGINE**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✨ *Analyze image properties & metadata.*\n\n"
        "📷 **What I check:**\n"
        "• Resolution & File Format\n"
        "• Color Mode & Dimensions\n"
        "• Available EXIF Tags (Camera, ISO, Lens)\n\n"
        "👉 *Just send any photo from your gallery or as a file!*"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Send an Image", callback_data="help_exif")]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data == "help_exif")
async def callback_help(callback: CallbackQuery):
    await callback.answer("Just send any image from your gallery or chat!", show_alert=True)

@dp.message(F.photo | F.document)
async def extract_exif(message: Message):
    status_msg = await message.answer("🔄 **Analyzing image data...**", parse_mode="Markdown")
    
    file_path = f"temp_{message.from_user.id}.jpg"
    
    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        else:
            if not message.document.mime_type or not message.document.mime_type.startswith('image/'):
                await status_msg.edit_text("❌ **Error:** Please send a valid image file.")
                return
            file_id = message.document.file_id
            
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=file_path)
        
        # Відкриваємо зображення через Pillow
        image = Image.open(file_path)
                # Базова інформація про файл (яка є завжди, навіть якщо EXIF вирізано)
        width, height = image.size
        img_format = image.format
        img_mode = image.mode
        file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
        
        report = [
            "📊 **IMAGE ANALYSIS REPORT**",
            "━━━━━━━━━━━━━━━━━━━",
            f"• **Format**: `{img_format}`",
            f"• **Resolution**: `{width}x{height} px`",
            f"• **Color Mode**: `{img_mode}`",
            f"• **File Size**: `{file_size_kb} KB`",
            "━━━━━━━━━━━━━━━━━━━",
            "📷 **EXIF Tags:**"
        ]
        
        # Намагаємося витягнути EXIF, якщо він є
        exif_data = image.getexif()
        found_exif = False
        
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    try:
                        value = value.decode(errors='ignore')
                    except:
                        value = "<binary data>"
                report.append(f"• **{tag}**: `{value}`")
                found_exif = True
                
        if not found_exif:
            report.append("ℹ️ *No deep EXIF tags found (compressed by messenger or screenshot).*")
            
        result_text = "\n".join(report[:25])
        
        done_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Analyze another", callback_data="help_exif")]
        ])
        
        await status_msg.edit_text(result_text, reply_markup=done_keyboard, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"Image Analysis Error: {e}")
        await status_msg.edit_text("❌ **Error:** Could not process this image.")
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("EXIF & Image Info Bot is online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
