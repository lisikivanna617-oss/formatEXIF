import asyncio
import logging
import os
import sys
import urllib.request
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Автоматичне завантаження справжніх шрифтів, якщо їх немає в системі
FONT_URLS = {
    "impact": "https://github.com/google/fonts/raw/main/apache/impact/Impact.ttf",
    "comic": "https://github.com/google/fonts/raw/main/ofl/comicsansms/ComicSansMS.ttf",
    "arial": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Black.ttf"
}

async def ensure_fonts():
    os.makedirs("fonts", exist_ok=True)
    for name, url in FONT_URLS.items():
        path = f"fonts/{name}.ttf"
        if not os.path.exists(path):
            try:
                urllib.request.urlretrieve(url, path)
            except Exception as e:
                logging.error(f"Failed to download font {name}: {e}")

# Локалізація (4 мови)
LANGS = {
    "en": {
        "title": "⚡ MEME GENERATOR ENGINE",
        "desc": "✨ Create classic memes with real fonts.",
        "step1": "1. Choose your language & font below.",
        "step2": "2. Send an image with caption: `Top text | Bottom text`",
        "success": "✅ Meme generated successfully!",
        "btn_font": "🔤 Font",
        "btn_lang": "🌐 Lang",
        "err": "❌ Error processing image."
    },
    "uk": {
        "title": "⚡ ГЕНЕРАТОР МЕМІВ",
        "desc": "✨ Створюй класичні меми зі справжніми шрифтами.",
        "step1": "1. Обери мову та шрифт нижче.",
        "step2": "2. Надішли фото з підписом: `Верхній текст | Нижній текст`",
        "success": "✅ Мем успішно створено!",
        "btn_font": "🔤 Шрифт",
        "btn_lang": "🌐 Мова",
        "err": "❌ Поשлка обробки зображення."
    },
    "ru": {
        "title": "⚡ ГЕНЕРАТОР МЕМОВ",
        "desc": "✨ Создавай классические мемы с реальными шрифтами.",
        "step1": "1. Выбери язык и шрифт ниже.",
        "step2": "2. Отправь фото с подписью: `Верхний текст | Нижний текст`",
        "success": "✅ Мем успешно создан!",
        "btn_font": "🔤 Шрифт",
        "btn_lang": "🌐 Язык",
        "err": "❌ Ошибка обработки изображения."
    },
    "pl": {
        "title": "⚡ GENERATOR MEMÓW",
        "desc": "✨ Twórz klasyczne memy z prawdziwymi czcionkami.",
        "step1": "1. Wybierz język i czcionkę poniżej.",
        "step2": "2. Wyślij zdjęcie z podpisem: `Tekst górny | Tekst dolny`",
        "success": "✅ Mem został utworzony!",
        "btn_font": "🔤 Czcionka",
        "btn_lang": "🌐 Język",
        "err": "❌ Błąd przetwarzania obrazu."
    }
}

user_prefs = {} # {user_id: {"lang": "uk", "font": "impact"}}

def get_pref(user_id):
    return user_prefs.setdefault(user_id, {"lang": "en", "font": "impact"})

def get_main_keyboard(lang):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔥 Impact", callback_data="f_impact"),
            InlineKeyboardButton(text="😜 Comic", callback_data="f_comic"),
            InlineKeyboardButton(text="📌 Roboto", callback_data="f_arial")
        ],
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

@dp.callback_query(F.data.startswith("f_"))
async def change_font(callback: CallbackQuery):
    font_name = callback.data.split("_")[1]
    pref = get_pref(callback.from_user.id)
    pref["font"] = font_name
    await callback.answer(f"Font changed to {font_name.upper()}!", show_alert=True)

@dp.callback_query(F.data.startswith("l_"))
async def change_lang(callback: CallbackQuery):
    lang_code = callback.data.split("_")[1]
    pref = get_pref(callback.from_user.id)
    pref["lang"] = lang_code
    
    t = LANGS[lang_code]
    text = f"**{t['title']}**\n━━━━━━━━━━━━━━━━━━━\n{t['desc']}\n\n📝 **Guide:**\n{t['step1']}\n{t['step2']}\n\n👉 *Send a photo now!*"
    await callback.message.edit_text(text, reply_markup=get_main_keyboard(lang_code), parse_mode="Markdown")
    await callback.answer(f"Language updated!")

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
        
        font_path = f"fonts/{pref['font']}.ttf"
        font_size = max(int(height / 10), 20)
        
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
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
    await ensure_fonts()
    print("Meme Generator Bot is fully loaded & online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
