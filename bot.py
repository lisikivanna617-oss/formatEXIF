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

# 10 великих, детальних та професійних шаблонів для генерації промтів
PROMPT_TEMPLATES = [
    # 1. Цифровий векторний арт / Мінімалізм
    lambda t: f"A striking high-end vector illustration of {t}, clean minimalist aesthetic, sharp clean lines, smooth vector curves, vibrant contrasting color palette, flat design with subtle modern gradients, professional graphic design, Behance featured, crisp details, 8k resolution, vector masterpiece --ar 1:1 --v 6.0",
    
    # 2. Кіберпанк / Неон
    lambda t: f"A futuristic cyberpunk concept art of {t}, glowing neon lights, holographic accents and data streams, dark gritty urban alleyway background, cinematic moody lighting, intricate sci-fi mechanical details, unreal engine 5 render, hyper-detailed, ray-tracing reflections, masterpiece --ar 16:9 --v 6.0",
    
    # 3. Кінематографічний фотореалізм
    lambda t: f"A breathtaking photorealistic cinematic shot of {t}, dramatic volumetric studio lighting, highly detailed textures, realistic depth of field, shot on 35mm lens, anamorphic flare, professional color grading, ultra-realistic skin and surface details, award-winning photography --ar 16:9 --v 6.0",
    
    # 4. Темне фентезі / Епік
    lambda t: f"An epic dark fantasy digital painting of {t}, mysterious atmosphere, gothic architecture elements, moody dramatic shadows, intricate armor and surface details, concept art by master artists, rich oil on canvas texture, dramatic lighting, highly detailed --ar 4:3 --v 6.0",
    
    # 5. Сучасне аніме / Манга
    lambda t: f"A vibrant modern anime art style of {t}, beautiful intricate cel shading, expressive clean lines, dynamic composition, glowing highlights, background art inspired by makoto shinkai, highly detailed, vivid saturated colors, visual novel cover art quality --ar 16:9 --v 6.0",
    
    # 6. 3D Pixar / Мільтплікаційний стиль
    lambda t: f"A charming premium 3D cartoon style of {t}, smooth clay-like subsurface scattering textures, soft studio three-point lighting, volumetric rendering, cute and playful design, octane render, pastel color palette, highly polished, smooth contours --ar 1:1 --v 6.0",
    
    # 7. Ретро синтвейв / 80-ті
    lambda t: f"An 80s retro synthwave aesthetic depiction of {t}, glowing neon grid lines, vibrant sunset gradient background, subtle VHS glitch effects, nostalgic purple and cyan color scheme, vintage cyberpunk vibe, sharp neon glow, retro-futuristic masterpiece --ar 16:9 --v 6.0",
    
    # 8. Класичний олійний живопис
    lambda t: f"A classical fine oil painting masterpiece featuring {t}, visible heavy textured brushstrokes, rich deep color palette, dramatic chiaroscuro lighting reminiscent of old masters, museum-quality artwork, canvas grain, profound depth --ar 4:3 --v 6.0",
    
    # 9. Мінімалістичний лайнарт
    lambda t: f"An elegant minimalist continuous line art of {t}, abstract geometric background shapes, sophisticated composition, delicate thin black ink strokes, modern wall art print style, clean white background, aesthetic vector lines --ar 1:1 --v 6.0",
    
    # 10. Високотехнологічний неоновий портрет
    lambda t: f"A high-end hyper-detailed studio concept of {t}, multi-colored vibrant rim lighting, futuristic industrial laboratory background, ultra-sharp focus, render-ready complex textures, cybernetic aesthetic, Unreal Engine 5 hyper-realism --ar 1:1 --v 6.0"
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
        "✨ *Massive AI Prompt Enhancer.*\n\n"
        "📝 *Send me any raw idea (e.g., 'gray cat avatar'), and I'll transform it into a massive, detailed, professional AI prompt!*"
    )
    await message.answer(welcome_text, reply_markup=get_keyboard(), parse_mode="Markdown")

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_prompt_generation(message: Message):
    raw_text = message.text.strip()
    
    # Вибираємо випадковий великий шаблон
    selected_template = random.choice(PROMPT_TEMPLATES)
    generated_prompt = selected_template(raw_text)
    
    response = (
        "✦ ─────────── ✧ ─────────── ✦\n"
        "🎯 **RAW IDEA:**\n"
        f"_{raw_text}_\n\n"
        "🚀 **MASSIVE ENHANCED PROMPT:**\n"
        f"`{generated_prompt}`\n"
        "✦ ─────────── ✧ ─────────── ✦\n\n"
        "💡 *Copy and paste this into Midjourney or DALL-E!*"
    )
    
    await message.answer(
        response,
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Formatify Massive Prompt Bot is online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
