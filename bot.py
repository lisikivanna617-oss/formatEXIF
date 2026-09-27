import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Локалізація (4 мови)
LANGS = {
    "en": {
        "title": "⚡ MEME GENERATOR ENGINE",
        "desc": "✨ Create classic memes with system fonts.",
        "step1": "1. Choose your language below.",
        "step2": "2. Send an image with caption: `Top text | Bottom text`",
        "success": "✅ Meme generated successfully!",
        "err": "❌ Error processing image."
    },
    "uk": {
        "title": "⚡ ГЕНЕРАТОР МЕМІВ",
        "desc": "✨ Створюй класичні меми з підтримкою кирилиці.",
        "step1": "1. Обери мову нижче.",
        "step2": "2. Надішли фото з підписом: `Верхній текст | Нижній текст`",
        "success": "✅ Мем успішно створено!",
        "err": "❌ Помилка обробки зображення."
    },
    "ru": {
        "title": "⚡ ГЕНЕРАТОР МЕМОВ",
        "desc": "✨ Создавай классические мемы с поддержкой кириллицы.",
        "step1": "1. Выбери язык ниже.",
        "step2": "2. Отправь фото с подписью: `Верхний текст | Нижний текст`",
        "success": "✅ Мем успешно создан!",
        "err": "❌ Ошибка обработки изображения."
    },
    "pl": {
        "title": "⚡ GENERATOR MEMÓW",
        "desc": "✨ Twórz klasyczne memy z polskimi znakami.",
        "step1": "1. Wybierz język poniżej.",
        "step2": "2. Wyślij zdjęcie z podpisem: `Tekst górny | Tekst dolny`",
        "success": "✅ Mem został utworzony!",
        "err": "❌ Błąd przetwarzania obrazu."
    }
}

user_prefs = {}

def get_pref(user_id):
    return user_prefs.setdefault(user_id, {"lang": "en"})

def get_main_keyboard(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇬🇧 EN", callback_data="l_en"),
            InlineKeyboardButton(text="🇺🇦 UA", callback_data="l_uk"),
            InlineKeyboardButton(text="🇷🇺 RU", callback_data="l_ru"),
            InlineKeyboardButton(text="🇵🇱 PL", callback_data="l_pl")
        ]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    pref = get_pref(message.from_user.id)
    t = LANGS[pref["lang"]]
    text = f"**{t['title']}**\n━━━━━━━━━━━━━━━━━━━\n{t['desc']}\n\n📝 **Guide:**\n{t['step1']}\n{t['step2']}\n\n👉 *Send a photo now!*"
    await message.answer(text, reply_markup=get_main_keyboard(pref["lang"]), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("l_"))
async def change_lang(callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    pref = get_pref(callback.from_user.id)
    pref["lang"] = lang_code
    t = LANGS[lang_code]
    text = f"**{t['title']}**\n━━━━━━━━━━━━━━━━━━━\n{t['desc']}\n\n📝 **Guide:**\n{t['step1']}\n{t['step2']}\n\n👉 *Send a photo now!*"
    try:
        await callback.message.edit_text(text, reply_markup=get_main_keyboard(lang_code), parse_mode="Markdown")
    except Exception:
        pass
    await callback.answer("Language updated!")

@dp.message(F.photo)
async def generate_meme(message: Message):
    pref = get_pref(message.from_user.id)
    t = LANGS[pref["lang"]]
    
    status_msg = await message.answer("🔄 **Rendering meme...**", parse_mode="Markdown")
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
        
        font_size = max(int(height / 10), 20)
        
        # Використовуємо гарантований системний шрифт Linux із підтримкою кирилиці
        font = None
        system_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
        ]
        
        for f_path in system_fonts:
            if os.path.exists(f_path):
                try:
                    font = ImageFont.truetype(f_path, font_size)
                    break
                except:
                    continue
                    
        if not font:
            font = ImageFont.load_default()

        def draw_text_with_outline(xy, text, font, draw):
            x, y = xy
            outline_range = max(int(font_size / 10), 3)
            for adj_x in range(-outline_range, outline_range + 1):
                for adj_y in range(-outline_range, outline_range + 1):
                    if adj_x != 0 or adj_y != 0:
                        draw.text((x + adj_x, y + adj_y), text, font=font, fill="black", anchor="mm", align="center")
            draw.text((x, y), text, font=font, fill="white", anchor="mm", align="center")

        if top_text:
            draw_text_with_outline((width / 2, height * 0.12), top_text, font, draw)
        if bottom_text:
            draw_text_with_outline((width / 2, height * 0.88), bottom_text, font, draw)
            
        img.save(output_path)
        
        with open(output_path, "rb") as meme_file:
            input_file = BufferedInputFile(meme_file.read(), filename="meme.jpg")
            await message.answer_photo(
                photo=input_file,
                caption=t["success"],
                reply_markup=get_main_keyboard(pref["lang"]),
                parse_mode="Markdown"
            )
        await status_msg.delete()
        
    except Exception as e:
        logging.error(f"Meme Error: {e}")
        await status_msg.edit_text(t["err"])
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(output_path):
            os.remove(output_path)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Meme Generator Bot is online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
        
