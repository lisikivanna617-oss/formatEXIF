import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Зберігаємо обраний стиль для кожного користувача (за замовчуванням 'vector')
user_selected_style = {}

# Словник з великими детальними шаблонами для кожного стилю
PROMPT_TEMPLATES = {
    "vector": lambda t: f"A striking high-end vector illustration of {t}, clean minimalist aesthetic, sharp clean lines, smooth vector curves, vibrant contrasting color palette, flat design with subtle modern gradients, professional graphic design, Behance featured, crisp details, 8k resolution, vector masterpiece --ar 1:1 --v 6.0",
    
    "cyberpunk": lambda t: f"A futuristic cyberpunk concept art of {t}, glowing neon lights, holographic accents and data streams, dark gritty urban alleyway background, cinematic moody lighting, intricate sci-fi mechanical details, unreal engine 5 render, hyper-detailed, ray-tracing reflections, masterpiece --ar 16:9 --v 6.0",
    
    "photo": lambda t: f"A breathtaking photorealistic cinematic shot of {t}, dramatic volumetric studio lighting, highly detailed textures, realistic depth of field, shot on 35mm lens, anamorphic flare, professional color grading, ultra-realistic skin and surface details, award-winning photography --ar 16:9 --v 6.0",
    
    "fantasy": lambda t: f"An epic dark fantasy digital painting of {t}, mysterious atmosphere, gothic architecture elements, moody dramatic shadows, intricate armor and surface details, concept art by master artists, rich oil on canvas texture, dramatic lighting, highly detailed --ar 4:3 --v 6.0",
    
    "anime": lambda t: f"A vibrant modern anime art style of {t}, beautiful intricate cel shading, expressive clean lines, dynamic composition, glowing highlights, background art inspired by makoto shinkai, highly detailed, vivid saturated colors, visual novel cover art quality --ar 16:9 --v 6.0",
    
    "pixar": lambda t: f"A charming premium 3D cartoon style of {t}, smooth clay-like subsurface scattering textures, soft studio three-point lighting, volumetric rendering, cute and playful design, octane render, pastel color palette, highly polished, smooth contours --ar 1:1 --v 6.0",
    
    "synthwave": lambda t: f"An 80s retro synthwave aesthetic depiction of {t}, glowing neon grid lines, vibrant sunset gradient background, subtle VHS glitch effects, nostalgic purple and cyan color scheme, vintage cyberpunk vibe, sharp neon glow, retro-futuristic masterpiece --ar 16:9 --v 6.0",
    
    "oil": lambda t: f"A classical fine oil painting masterpiece featuring {t}, visible heavy textured brushstrokes, rich deep color palette, dramatic chiaroscuro lighting reminiscent of old masters, museum-quality artwork, canvas grain, profound depth --ar 4:3 --v 6.0",
    
    "lineart": lambda t: f"An elegant minimalist continuous line art of {t}, abstract geometric background shapes, sophisticated composition, delicate thin black ink strokes, modern wall art print style, clean white background, aesthetic vector lines --ar 1:1 --v 6.0",
    
    "portrait": lambda t: f"A high-end hyper-detailed studio concept of {t}, multi-colored vibrant rim lighting, futuristic industrial laboratory background, ultra-sharp focus, render-ready complex textures, cybernetic aesthetic, Unreal Engine 5 hyper-realism --ar 1:1 --v 6.0"
}

def get_styles_keyboard(current_style: str = "vector"):
    # Створюємо зручну сітку з кнопок стилів із позначкою вибраного
    styles = [
        ("vector", "🔹 Vector Art"),
        ("cyberpunk", "⚡ Cyberpunk"),
        ("photo", "📸 Photorealistic"),
        ("fantasy", "🗡️ Dark Fantasy"),
        ("anime", "✨ Anime Style"),
        ("pixar", "🧸 3D Pixar"),
        ("synthwave", "🌆 Synthwave 80s"),
        ("oil", "🖼️ Oil Painting"),
        ("lineart", "✏️ Line Art"),
        ("portrait", "💡 Neon Portrait")
    ]
    
    keyboard = []
    row = []
    for code, name in styles:
        prefix = "✅ " if code == current_style else ""
        row.append(InlineKeyboardButton(text=f"{prefix}{name}", callback_data=f"style_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_selected_style[message.from_user.id] = "vector"
    welcome_text = (
        "✦ ─────────── ⚡ ─────────── ✦\n"
        "       🤖 **FORMATIFY BOT**       \n"
        "✦ ─────────── ⚡ ─────────── ✦\n\n"
        "✨ *Interactive AI Prompt Enhancer.*\n\n"
        "👇 *Choose your preferred style below, then send me your raw idea (e.g., 'gray cat avatar')!*"
    )
    await message.answer(welcome_text, reply_markup=get_styles_keyboard("vector"), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("style_"))
async def set_user_style(callback: CallbackQuery):
    style_code = callback.data.split("_")[1]
    user_selected_style[callback.from_user.id] = style_code
    
    await callback.answer(f"Style selected: {style_code.upper()}", show_alert=True)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=get_styles_keyboard(style_code))
    except Exception:
        pass

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_prompt_generation(message: Message):
    user_id = message.from_user.id
    current_style = user_selected_style.get(user_id, "vector")
    raw_text = message.text.strip()
    
    # Генеруємо промт на основі обраного користувачем стилю
    template_func = PROMPT_TEMPLATES.get(current_style, PROMPT_TEMPLATES["vector"])
    generated_prompt = template_func(raw_text)
    
    response = (
        "✦ ─────────── ✧ ─────────── ✦\n"
        f"🎯 **RAW IDEA:** _{raw_text}_\n"
        f"🎨 **STYLE:** `{current_style.upper()}`\n\n"
        "🚀 **MASSIVE ENHANCED PROMPT:**\n"
        f"`{generated_prompt}`\n"
        "✦ ─────────── ✧ ─────────── ✦\n\n"
        "💡 *Copy and paste this into Midjourney or DALL-E!*"
    )
    
    await message.answer(
        response,
        reply_markup=get_styles_keyboard(current_style),
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Formatify Interactive Prompt Bot is online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
