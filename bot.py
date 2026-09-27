import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "⚡ **FORMATIFY BOT**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✨ *Your personal assistant for formatting Telegram posts.*\n\n"
        "📝 **How to use:**\n"
        "Just send me your raw text, and I will format it into a clean, ready-to-publish post with your signature style!\n\n"
        "👉 *Send your text below:*"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 My Channel", url="https://t.me/corvain_games")]
    ])
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

@dp.message(F.text & ~F.text.startswith("/"))
async def format_post(message: Message):
    raw_text = message.text
    
    # Можеш додати сюди будь-яку логіку форматування, наприклад:
    # - Автоматичне виправлення якихось символів
    # - Додавання красивих відступів тощо
    
    # Додаємо фірмовий підпис або футер до кожного поста
    formatted_text = (
        f"{raw_text}\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Formatted via @Formatify_Bot*"
    )
    
    # Кнопки під пост (наприклад, кнопка копіювання або переходу)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Created with Formatify", url="https://t.me/Formatify_Bot")]
    ])
    
    await message.answer(
        f"✅ **Ready post:**\n\n{formatted_text}",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Formatify Bot is online!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
