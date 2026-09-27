import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FleshedOut
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словник доступних шрифтів (шляхи для Linux/Railway та можливі fallback варіанти)
FONTS = {
    "impact": {
        "name": "🔥 Impact (Classic)",
        "paths": [
            "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "impact.ttf"
        ]
    },
    "arial": {
        "name": "📌 Arial Bold",
        "paths": [
            "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "arial.ttf"
        ]
    },
    "comic": {
        "name": "😜 Comic Sans",
        "paths": [
            "/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "comic.ttf"
        ]
    }
}

# Зберігаємо тимчасово обраний шрифт для користувача (за замовчуванням impact)
user_fonts = {}

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "⚡ **MEME GENERATOR ENGINE**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✨ *Create classic memes with custom fonts.*\n\n"
        "📝 **How to use:**\n"
        "1. Select your preferred font below.\n"
        "2. Send an image with caption: `Top text | Bottom text`\n"
        "3. Get your styled meme instantly!\n\n"
        "👉 *Choose a font to get started:*"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔥 Impact", callback_data="font_impact"),
            InlineKeyboardButton(text="📌 Arial", callback_data="font_arial"),
            InlineKeyboardButton(text="😜 Comic", callback_data="font_comic")
        ]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.callback_query(F.data.startswith("font_"))
async def set_user_font(callback: CallbackQuery):
    font_key = callback.data.split("_")[1]
    user_fonts[callback.from_user.id] = font_key
    
    font_name = FONTS[font_key]["name"]
    await callback.answer(f"Font changed to {font_name}!", show_alert=True)
    
    await callback.message.edit_text(
        f"⚡ **MEME GENERATOR ENGINE**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"✨ *Active font:* `{font_name}`\n\n"
        f"👉 *Now send any photo with text like: `Top text | Bottom text`*",
        reply_markup=callback.message.reply_markup,
        parse_mode="Markdown"
    )

@dp.message(F.photo)
async def generate_meme(message: Message):
    status_msg = await message.answer("🔄 **Rendering meme with style...**", parse_mode="Markdown")
    
    file_path = f"temp_{message.from_user.id}.jpg"
    output_path = f"meme_{message.from_user.id}.jpg"
    
    try:
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=file_path)
        
        caption = message.caption or "Мем | Готово"
        if "|" in caption:
            parts = caption.split("|", 1)
            top_text = parts[0].strip().upper()
            bottom_text = parts[1].strip().upper()
        else:
            top_text = caption.strip().upper()
            bottom_text = ""
            
        img = Image.open(file_path)
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Визначаємо обраний шрифт користувача (за замовчуванням impact)
        user_choice = user_fonts.get(message.from_user.id, "impact")
        font_paths = FONTS[user_choice]["paths"]
        
        font = None
        font_size = max(int(height / 10), 20)
        
        for path in font_paths:
            try:
                font = ImageFont.truetype(path, font_size)
                break
            except:
                continue
                
        if not font:
            font = ImageFont.load_default()

        def draw_text_with_outline(xy, text, font, draw):
            x, y = xy
            # Товсте чорне обведення для класичного стилю мему
            outline_range = max(int(font_size / 12), 2)
            for adj_x in range(-outline_range, outline_range + 1):
                for adj_y in range(-outline_range, outline_range + 1):
                    if adj_x != 0 or adj_y != 0:
                        draw.text((x + adj_x, y + adj_y), text, font=font, fill="black", anchor="mm", align="center")
            # Білий текст поверх обведення
            draw.text((x, y), text, font=font, fill="white", anchor="mm", align="center")

        # Малюємо верхній текст
        if top_text:
            draw_text_with_outline((width / 2, height * 0.12), top_text, font, draw)
            
        # Малюємо нижній текст
        if bottom_text:
            draw_text_with_outline((width / 2, height * 0.88), bottom_text, font, draw)
            
        img.save(output_path)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Make another", callback_data="font_impact")]
        ])
        
        with open(output_path, "rb") as meme_file:
            input_file = BufferedInputFile(meme_file.read(), filename="meme.jpg")
            await message.answer_photo(
                photo=input_file,
                caption="✅ **Meme generated successfully!**",
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            
        await status_msg.delete()
        
    except Exception as e:
        logging.error(f"Meme Error: {e}")
        await status_msg.edit_text("❌ **Error:** Could not process this image.")
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(output_path):
            os.remove(output_path)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Meme Generator Bot with Fonts is online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
