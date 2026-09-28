import asyncio
import logging
import os
import sys
from urllib.parse import urlparse, urlunparse
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Зберігаємо режим роботи для кожного користувача (link або text)
user_modes = {}

def get_main_keyboard(current_mode: str = "link"):
    link_mark = "✅ " if current_mode == "link" else ""
    text_mark = "✅ " if current_mode == "text" else ""
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{link_mark}☍ Clean Link", callback_data="mode_link"),
            InlineKeyboardButton(text=f"{text_mark}⊹ Format Text", callback_data="mode_text")
        ]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "✦ ─────────── ϟ ─────────── ✦\n"
        "       🤖 **FORMATIFY BOT**       \n"
        "✦ ─────────── ϟ ─────────── ✦\n\n"
        "☑ *Your everyday assistant for cleaning links and formatting text.*\n\n"
        "👇 *Choose a mode below and send your message:*"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard("link"), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("mode_"))
async def set_mode(callback: CallbackQuery):
    mode = callback.data.split("_")[1]
    user_modes[callback.from_user.id] = mode
    
    mode_name = "Link Cleaner ☍" if mode == "link" else "Text Formatter ⊹"
    await callback.answer(f"Mode changed to: {mode_name}", show_alert=True)
    
    try:
        await callback.message.edit_reply_markup(reply_markup=get_main_keyboard(mode))
    except Exception:
        pass

def clean_url(url_str: str) -> str:
    try:
        parsed = urlparse(url_str.strip())
        if not parsed.scheme:
            parsed = urlparse("https://" + url_str.strip())
        
        clean_netloc = parsed.netloc
        clean_path = parsed.path
        
        # Прибираємо зайві параметри відстеження
        clean_query = "" 
            
        cleaned = urlunparse((parsed.scheme, clean_netloc, clean_path, parsed.params, clean_query, ""))
        return cleaned if cleaned else url_str
    except Exception:
        return url_str

def format_clean_text(text: str) -> str:
    lines = text.split("\n")
    formatted = ["✦ ─────────── ✧ ─────────── ✦", ""]
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted.append("")
            continue
            
        if stripped.startswith("- ") or stripped.startswith("* "):
            formatted.append(f"• {stripped[2:].strip()}")
        else:
            formatted.append(stripped)
            
    formatted.extend(["", "✦ ─────────── ✧ ─────────── ✦", "💡 *Formatted via @formatify_bot*"])
    return "\n".join(formatted)

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message):
    user_id = message.from_user.id
    mode = user_modes.get(user_id, "link")
    text = message.text
    
    if mode == "link":
        cleaned = clean_url(text)
        response = (
            "🔗 **Clean Link:**\n"
            f"`{cleaned}`\n\n"
            "✨ *All tracking tails and parameters removed!*"
        )
    else:
        response = format_clean_text(text)
        
    await message.answer(
        response,
        reply_markup=get_main_keyboard(mode),
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Formatify Bot is online in English!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
