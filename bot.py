import asyncio
import logging
import os
import random
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 10 різних великих шаблонів для генерації промтів
PROMPT_TEMPLATES = [
    # 1. Digital Vector Art / Minimalist
    lambda t: f"A striking vector illustration of {t}, clean minimalist aesthetic, sharp lines, smooth vector curves, vibrant contrasting colors, flat design with subtle gradients, professional graphic design,behance featured, 8k resolution --ar 1:1",
    
    # 2. Cyberpunk / Neon
    lambda t: f"A futuristic cyberpunk concept art of {t}, glowing neon lights, holographic accents, dark gritty urban background, cinematic moody lighting, intricate sci-fi details, unreal engine 5 render, hyper-detailed, masterpiece --ar 16:9",
    
    # 3. Cinematic Photorealistic
    lambda t: f"A breathtaking photorealistic cinematic shot of {t}, dramatic volumetric lighting, highly detailed textures, depth of field, shot on 35mm lens, professional color grading, ultra-realistic, award-winning photography --ar 16:9",
    
    # 4. Dark Fantasy / Epic
    lambda t: f"An epic dark fantasy digital painting of {t}, mysterious atmosphere, gothic architecture elements, moody dramatic shadows, intricate armor and surface details, concept art by Greg Rutkowski, oil on canvas texture --ar 4:3",
    
    # 5. Anime / Manga Style
    lambda t: f"A vibrant modern anime art style of {t}, beautiful cel shading, expressive lines, dynamic composition, glowing highlights, background art by Makoto Shinkai, highly detailed, vivid saturated colors --ar 16:9",
    
    # 6. 3D Pixar / Cute Style
    lambda t: f"A charming 3D cartoon style of {t}, smooth clay-like textures, soft studio lighting, volumetric rendering, cute and playful design, octane render, pastel color palette, highly polished --ar 1:1",
    
    # 7. Retro Synthwave / 80s
    lambda t: f"An 80s retro synthwave aesthetic depiction of {t}, neon grid lines, sunset gradient background, VHS glitch effects, vibrant purple and cyan color scheme, nostalgic cyberpunk vibe, sharp details --ar 16:9",
    
    # 8. Oil Painting / Classical
    lambda t: f"A classical oil painting masterpiece featuring {t}, visible heavy brushstrokes, rich deep color palette, dramatic chiaroscuro lighting reminiscent of Rembrandt, museum-quality fine art --ar 4:3",
    
    # 9. Minimalist Line Art
    lambda t: f"An elegant minimalist continuous line art of {t}, abstract geometric background shapes, sophisticated composition, delicate thin ink strokes, modern wall art print style --ar 1:1",
    
    # 10. Moody Neon Portrait / High-Tech
    lambda t: f"A high-end hyper-detailed studio concept of {t}, multi-colored rim lighting, futuristic industrial background, ultra-sharp focus, render-ready textures, cybernetic aesthetic --ar 1:1"
]

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ @Formatify_Bot", url="https://t.me/Formatify_Bot")]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "✦ ─────────── ⚡ ─────────── ✦\n"
        "       🤖 **FORMATIFY BOT**       \n"
        "✦ ─────────── ⚡ ─────────── ✦\n\n"
        "✨ *Advanced AI Prompt Enhancer.*\n\n"
        "📝 *Send me any raw idea (e.g., 'gray cat avatar'), and I'll randomly transform it into one of 10 massive, professional AI prompts!*"
    )
    await message.answer(welcome_text, reply_markup=get_keyboard(), parse_mode="Markdown")

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_prompt_generation(message: Message):
    raw_text = message.text.strip()
    
    # Вибираємо випадковий шаблон з 10 доступних
    selected_template = random.choice(PROMPT_TEMPLATES)
    generated_prompt = selected_template(raw_text)
    
    response = (
        "✦ ─────────── ✧ ─────────── ✦\n"
        "🎯 **RAW IDEA:**\n"
        f"_{raw_text}_\n\n"
        "🚀 **ENHANCED PROMPT (Expanded & Randomized):**\n"
        f"`{generated_prompt}`\n"
        "✦ ─────────── ✧ ─────────── ✦\n\n"
        "💡 *Copy and paste this into Midjourney, DALL-E, or Stable Diffusion!*"
    )
    
    await message.answer(
        response,
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Formatify Prompt Bot is online with 10 variations!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
