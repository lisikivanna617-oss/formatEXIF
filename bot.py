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

# Зберігаємо вибраний стиль користувача (за замовчуванням tech)
user_styles = {}

def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ Tech / Gaming", callback_data="style_tech"),
            InlineKeyboardButton(text="📌 Minimal", callback_data="style_minimal")
        ]
    ])

@dp.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "⚡ **FORMATIFY BOT**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "✨ *Your personal channel post formatter.*\n\n"
        "📝 *Send me your raw text, and I'll turn it into a clean, structured post instantly!*"
    )
    await message.answer(welcome_text, reply_markup=get_keyboard(), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("style_"))
async def set_style(callback: CallbackQuery):
    style = callback.data.split("_")[1]
    user_styles[callback.from_user.id] = style
    style_name = "Tech / Gaming ⚡" if style == "tech" else "Minimal 📌"
    await callback.answer(f"Style changed to {style_name}!", show_alert=True)

def process_text(text: str, style: str) -> str:
    lines = text.split("\n")
    formatted_lines = []
    
    # Робимо перший рядок жирним заголовоком
    if lines:
        title = lines[0].strip().upper()
        if style == "tech":
            formatted_lines.append(f"🔥 **{title}**\n━━━━━━━━━━━━━━━━━━━")
        else:
            formatted_lines.append(f"▪️ **{title}**")
        lines = lines[1:]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted_lines.append("")
            continue
            
        # Автоматично перетворюємо пункти з дефісом або зірочкою на гарні списки
        if stripped.startswith("- ") or stripped.startswith("* "):
            clean_item = stripped[2:].strip()
            if style == "tech":
                formatted_lines.append(f"🔹 {clean_item}")
            else:
                formatted_lines.append(f"▫️ {clean_item}")
        else:
            formatted_lines.append(stripped)
            
    # Додаємо футер залежно від стилю
    if style == "tech":
        formatted_lines.append("\n━━━━━━━━━━━━━━━━━━━\n💡 *Via @Formatify_Bot*")
    else:
        formatted_lines.append("\n_@Formatify_Bot_")
        
    return "\n".join(formatted_lines)

@dp.message(F.text & ~F.text.startswith("/"))
async def format_post(message: Message):
    user_id = message.from_user.id
    style = user_styles.get(user_id, "tech")
    
    result_text = process_text(message.text, style)
    
    await message.answer(
        result_text,
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Formatify Bot is online with auto-formatting!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    
