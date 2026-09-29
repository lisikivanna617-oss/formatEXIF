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

# Зберігаємо обраний стиль для кожного користувача
user_selected_style = {}

# Сучасні, соковиті та величезні шаблони промтів
PROMPT_TEMPLATES = {
    "artistic": lambda t: f"A breathtaking modern digital illustration of {t}, rich painterly textures combined with crisp modern lines, expressive artistic brushwork, sophisticated color grading, dramatic atmospheric lighting, concept art masterpiece, trending on ArtStation, ultra-detailed, 8k resolution, cinematic composition --ar 16:9 --v 6.0",
    
    "webtoon": lambda t: f"A stunning modern webtoon and manhwa style illustration of {t}, clean polished linework, vibrant rich colors, gorgeous cel-shading with soft gradients, dramatic soft rim lighting, highly detailed character design, web comic cover art quality, visual storytelling masterpiece --ar 16:9 --v 6.0",
    
    "concept": lambda t: f"A high-end cinematic concept art of {t}, complex environment design, moody atmospheric haze, volumetric lighting rays, intricate surface textures, masterpiece created by industry veteran concept artists, Unreal Engine 5 render aesthetic, hyper-detailed depth --ar 16:9 --v 6.0",
    
    "dark_fantasy": lambda t: f"A dark epic fantasy digital painting of {t}, moody gothic atmosphere, deep shadows with subtle glowing highlights, intricate ornate details, rich oil-on-canvas texture mixed with modern digital lighting, dramatic chiaroscuro, museum-grade fantasy art --ar 4:3 --v 6.0",
    
    "stylized_3d": lambda t: f"A modern stylized 3D render of {t}, gorgeous clay and matte surface textures, soft studio subsurface scattering, premium artistic toy design aesthetic, octane render, beautiful pastel and neon color harmony, smooth organic contours, highly polished --ar 1:1 --v 6.0",
    
    "cyber_punk": lambda t: f"A next-gen cyberpunk aesthetic of {t}, hyper-detailed futuristic elements, complex holographic displays, moody rainy street reflections, neon glow, cinematic depth of field, ray-traced lighting, gritty yet clean sci-fi masterpiece --ar 16:9 --v 6.0",
    
    "anime_modern": lambda t: f"A high-end modern anime key visual featuring {t}, breathtaking background art inspired by Makoto Shinkai, luminous lighting, vibrant saturated colors, emotional atmosphere, exquisite detail in every element, crisp outlines, visual novel masterpiece --ar 16:9 --v 6.0",
    
    "minimal_vector": lambda t: f"A sleek modern vector art design of {t}, clean geometric shapes, sophisticated minimalist composition, flat design with smooth multi-layer gradients, elegant color palette, professional graphic branding style, crisp vector curves --ar 1:1 --v 6.0",
    
    "cinematic": lambda t: f"An ultra-detailed cinematic frame of {t}, shot on 35mm lens, anamorphic lens flare, professional Hollywood color grading, rich textures, incredible depth of field, dramatic moody atmosphere, award-winning cinematography --ar 16:9 --v 6.0",
    
    "neon_portrait": lambda t: f"A stunning stylized artistic portrait of {t}, vibrant dual-tone neon rim lighting, deep contrasting background, highly detailed facial features and textures, modern pop-culture aesthetic, professional studio lighting setup --ar 1:1 --v 6.0"
}

def get_styles_keyboard(current_style: str = "artistic"):
    styles = [
        ("artistic", "🎨 Artistic Paint"),
        ("webtoon", "📖 Webtoon / Manhwa"),
        ("concept", "🏛️ Concept Art"),
        ("dark_fantasy", "🗡️ Dark Fantasy"),
        ("stylized_3d", "🧊 Modern 3D"),
        ("cyber_punk", "⚡ Next-Gen Cyber"),
        ("anime_modern", "✨ Modern Anime"),
        ("minimal_vector", "📐 Clean Vector"),
        ("cinematic", "🎬 Cinematic Shot"),
        ("neon_portrait", "💡 Neon Portrait")
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
    user_selected_style[message.from_user.id] = "artistic"
    welcome_text = (
        "✦ ─────────── ⚡ ─────────── ✦\n"
        "       🤖 **FORMATIFY BOT**       \n"
        "✦ ─────────── ⚡ ─────────── ✦\n\n"
        "✨ *Modern Massive AI Prompt Enhancer.*\n\n"
        "👇 *Choose a modern style below, then send your raw idea (e.g., 'gray cat avatar')!*"
    )
    await message.answer(welcome_text, reply_markup=get_styles_keyboard("artistic"), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("style_"))
async def set_user_style(callback: CallbackQuery):
    style_code = callback.data.split("_")[1]
    user_selected_style[callback.from_user.id] = style_code
    
    await callback.answer(f"Style: {style_code.upper()}", show_alert=True)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=get_styles_keyboard(style_code))
    except Exception:
        pass

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_prompt_generation(message: Message):
    user_id = message.from_user.id
    current_style = user_selected_style.get(user_id, "artistic")
    raw_text = message.text.strip()
    
    template_func = PROMPT_TEMPLATES.get(current_style, PROMPT_TEMPLATES["artistic"])
    generated_prompt = template_func(raw_text)
    
    response = (
        "✦ ─────────── ✧ ─────────── ✦\n"
        f"🎯 **RAW IDEA:** _{raw_text}_\n"
        f"🎨 **STYLE:** `{current_style.upper()}`\n\n"
        "🚀 **MASSIVE PROMPT:**\n"
        f"`{generated_prompt}`\n"
        "✦ ─────────── ✧ ─────────── ✦\n\n"
        "💡 *Copy and paste into Midjourney or DALL-E!*"
    )
    
    await message.answer(
        response,
        reply_markup=get_styles_keyboard(current_style),
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Formatify Modern Prompt Bot is online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
