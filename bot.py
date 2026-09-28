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
        "✨ *AI Prompt Enhancer & Formatter.*\n\n"
        "📝 *Send me a raw, messy idea (e.g., 'gray cat avatar as a drawing'), and I'll turn it into a professional, high-quality prompt for AI image generators!*"
    )
    await message.answer(welcome_text, reply_markup=get_keyboard(), parse_mode="Markdown")

def enhance_prompt(raw_text: str) -> str:
    # Тут можна налаштувати логіку перетворення або розширення
    # Для прикладу робимо базовий якісний шаблон на основі введеного тексту
    cleaned = raw_text.strip()
    
    # Створюємо професійний промт (додаємо стилізацію, якість, деталі)
    enhanced = (
        f"A professional avatar design of {cleaned}, "
        f"vector style, clean minimalist background, vibrant colors, "
        f"high resolution, detailed digital art, masterpiece --ar 1:1"
    )
    
    return enhanced

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_prompt_generation(message: Message):
    raw_text = message.text
    generated_prompt = enhance_prompt(raw_text)
    
    response = (
        "✦ ─────────── ✧ ─────────── ✦\n"
        "🎯 **RAW IDEA:**\n"
        f"_{raw_text}_\n\n"
        "🚀 **ENHANCED PROMPT:**\n"
        f"`{generated_prompt}`\n"
        "✦ ─────────── ✧ ─────────── ✦\n\n"
        "💡 *Copy and paste this into Midjourney, DALL-E, or ChatGPT!*"
    )
    
    await message.answer(
        response,
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Formatify Prompt Bot is online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
