import asyncio
import io
import logging
import os
import threading

from flask import Flask
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    BufferedInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from PIL import Image


# =========================================================
# CONFIG
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


bot = Bot(TOKEN)
dp = Dispatcher()

# Temporary image storage
images = {}


# =========================================================
# RENDER WEB SERVER
# =========================================================

app = Flask(__name__)


@app.route("/")
def home():
    return "IMGFORCE is running!"


@app.route("/health")
def health():
    return {
        "status": "ok",
        "bot": "IMGFORCE"
    }


def run_web():
    port = int(os.getenv("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# =========================================================
# KEYBOARDS
# =========================================================

def start_page_keyboard(page: int):
    buttons = []
    
    if page == 1:
        nav_row = [
            InlineKeyboardButton(text="1/3", callback_data="start_page_1"),
            InlineKeyboardButton(text="➡️ Next", callback_data="start_page_2"),
        ]
    elif page == 2:
        nav_row = [
            InlineKeyboardButton(text="⬅️ Back", callback_data="start_page_1"),
            InlineKeyboardButton(text="2/3", callback_data="start_page_2"),
            InlineKeyboardButton(text="Next ➡️", callback_data="start_page_3"),
        ]
    else:  # page == 3
        nav_row = [
            InlineKeyboardButton(text="⬅️ Back", callback_data="start_page_2"),
            InlineKeyboardButton(text="3/3", callback_data="start_page_3"),
        ]
        
    buttons.append(nav_row)
    
    buttons.append([
        InlineKeyboardButton(
            text="🚀 Open Tools Menu", 
            callback_data="back"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⚡️ Compress", callback_data="compress"),
                InlineKeyboardButton(text="📐 Resize", callback_data="resize"),
            ],
            [
                InlineKeyboardButton(text="🧩 Split", callback_data="split"),
                InlineKeyboardButton(text="🔄 Convert", callback_data="convert"),
            ],
            [
                InlineKeyboardButton(text="✂️ Crop", callback_data="crop"),
                InlineKeyboardButton(text="ℹ️ Info", callback_data="info"),
            ],
            [
                InlineKeyboardButton(text="🧹 Clean EXIF", callback_data="exif"),
                InlineKeyboardButton(text="🔄 Rotate", callback_data="rotate"),
            ],
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="◀️ Back to menu",
                    callback_data="back"
                )
            ]
        ]
    )


# =========================================================
# START PAGES CONTENT & HANDLERS
# =========================================================

START_PAGES = {
    1: (
        "✨ Welcome to IMGFORCE! (1/3)\n\n"
        "Your all-in-one Telegram toolkit for quick and efficient image processing.\n\n"
        "👤 Owner & Developer: @vanishedhunter\n"
        "⚡️ Status: Online & Ready\n\n"
        "Use the arrows below to learn more or send a photo to get started right away!"
    ),
    2: (
        "🛠 Key Features Overview (2/3)\n\n"
        "⚡️ Compress — optimize image size without quality loss\n"
        "📐 Resize — change resolution according to your needs\n"
        "🧩 Split — divide pictures into equal grid parts\n"
        "🔄 Convert — switch between JPG, PNG, and WEBP\n"
        "✂️ Crop — trim image to custom aspect ratios\n"
        "🧹 Clean EXIF — remove hidden metadata for privacy\n"
        "🔄 Rotate — adjust photo orientation instantly"
    ),
    3: (
        "💡 How to Use (3/3)\n\n"
        "1. Simply attach and send any photo into this chat.\n"
        "2. Choose your desired action from the interactive menu.\n"
        "3. Download your freshly processed file!\n\n"
        "📩 For support or feedback, contact: @vanishedhunter"
    )
}


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        START_PAGES[1],
        reply_markup=start_page_keyboard(1)
    )


@dp.callback_query(F.data.startswith("start_page_"))
async def process_start_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    
    await callback.message.edit_text(
        START_PAGES[page],
        reply_markup=start_page_keyboard(page)
    )
    await callback.answer()


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        START_PAGES[2],
        reply_markup=start_page_keyboard(2)
    )
# =========================================================
# IMAGE HELPERS
# =========================================================

def get_image(user_id: int):
    if user_id not in images:
        return None

    try:
        image = Image.open(
            io.BytesIO(images[user_id])
        )
        image.load()
        return image
    except Exception:
        return None


def image_to_bytes(image: Image.Image, fmt="PNG", quality=90):
    output = io.BytesIO()
    fmt = fmt.upper()

    if fmt in ("JPG", "JPEG"):
        if image.mode not in ("RGB", "L"):
            if "A" in image.getbands():
                background = Image.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")

        image.save(output, format="JPEG", quality=quality, optimize=True)

    elif fmt == "WEBP":
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")

        image.save(output, format="WEBP", quality=quality, method=6)

    else:
        image.save(output, format=fmt)

    output.seek(0)
    return output.read()


async def send_image(message: Message, data: bytes, filename: str):
    await message.answer_document(
        BufferedInputFile(data, filename=filename)
    )


# =========================================================
# RECEIVE PHOTO
# =========================================================

@dp.message(F.photo)
async def receive_photo(message: Message):
    photo = message.photo[-1]

    try:
        file = await bot.get_file(photo.file_id)
        data = await bot.download_file(file.file_path)

        images[message.from_user.id] = data.getvalue()
        image = get_image(message.from_user.id)

        if image is None:
            await message.answer("❌ Failed to process this image.")
            return

        await message.answer(
            "✅ Photo uploaded successfully!\n\n"
            f"• Dimensions: {image.width} × {image.height} px\n"
            f"• Format: {image.format}\n\n"
            "Select an operation below:",
            reply_markup=main_keyboard()
        )

    except Exception as e:
        logging.exception(e)
        await message.answer("❌ Error downloading the photo.")


# =========================================================
# INFO
# =========================================================

@dp.callback_query(F.data == "info")
async def image_info(callback: CallbackQuery):
    user_id = callback.from_user.id
    image = get_image(user_id)

    if image is None:
        await callback.answer("Please send a photo first!", show_alert=True)
        return

    size_kb = len(images[user_id]) / 1024
    ratio = image.width / image.height

    await callback.message.answer(
        "📊 Image Details:\n\n"
        "👤 Owner: @vanishedhunter\n"
        f"⚙️ Format: {image.format}\n"
        f"📐 Dimensions: {image.width} × {image.height} px\n"
        f"🎨 Color Mode: {image.mode}\n"
        f"💾 File Size: {size_kb:.2f} KB\n"
        f"🖼 Aspect Ratio: {ratio:.2f}\n\n"
        "Need to process another image? Simply send a new photo!"
    )
    await callback.answer()


# =========================================================
# COMPRESS
# =========================================================

@dp.callback_query(F.data == "compress")
async def compress_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="High (85%)", callback_data="compress_85"),
                InlineKeyboardButton(text="Medium (60%)", callback_data="compress_60"),
                InlineKeyboardButton(text="Low (40%)", callback_data="compress_40"),
            ],
            [InlineKeyboardButton(text="◀️ Back", callback_data="back")]
        ]
    )

    await callback.message.answer(
        "⚡️ Compression Settings\n\nChoose compression level:",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("compress_"))
async def compress_image(callback: CallbackQuery):
    user_id = callback.from_user.id
    image = get_image(user_id)

    if image is None:
        await callback.answer("Please send a photo first!", show_alert=True)
        return

    quality = int(callback.data.split("_")[1])
    data = image_to_bytes(image, "JPEG", quality)

    await send_image(callback.message, data, f"compressed_{quality}.jpg")
    await callback.answer("Done! Image compressed.")


# =========================================================
# RESIZE
# =========================================================

@dp.callback_query(F.data == "resize")
async def resize_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1920 px", callback_data="resize_1920"),
                InlineKeyboardButton(text="1280 px", callback_data="resize_1280"),
            ],
            [
                InlineKeyboardButton(text="720 px", callback_data="resize_720"),
                InlineKeyboardButton(text="500 px", callback_data="resize_500"),
            ],
            [InlineKeyboardButton(text="◀️ Back", callback_data="back")]
        ]
    )

    await callback.message.answer(
        "📐 Resize Image\n\nChoose target maximum width:",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("resize_"))
async def resize_image(callback: CallbackQuery):
    user_id = callback.from_user.id
    image = get_image(user_id)

    if image is None:
        await callback.answer("Please send a photo first!", show_alert=True)
        return

    max_width = int(callback.data.split("_")[1])

    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

    data = image_to_bytes(image, "PNG")
    await send_image(callback.message, data, f"resized_{image.width}x{image.height}.png")
    await callback.answer("Done! Image resized.")


# =========================================================
# SPLIT
# =========================================================

@dp.callback_query(F.data == "split")
async def split_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="2 parts", callback_data="split_2"),
                InlineKeyboardButton(text="3 parts", callback_data="split_3"),
            ],
            [
                InlineKeyboardButton(text="4 parts (2x2)", callback_data="split_4"),
                InlineKeyboardButton(text="6 parts (3x2)", callback_data="split_6"),
            ],
            [InlineKeyboardButton(text="9 parts (3x3)", callback_data="split_9")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="back")]
        ]
    )

    await callback.message.answer(
        "🧩 Split Image\n\nChoose grid division:",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("split_"))
async def split_image(callback: CallbackQuery):
    user_id = callback.from_user.id
    image = get_image(user_id)

    if image is None:
        await callback.answer("Please send a photo first!", show_alert=True)
        return

    count = int(callback.data.split("_")[1])

    if count in (2, 3):
        columns, rows = count, 1
    elif count == 4:
        columns, rows = 2, 2
    elif count == 6:
        columns, rows = 3, 2
    else:
        columns, rows = 3, 3

    width, height = image.size

    for row in range(rows):
        for column in range(columns):
            left = round(column * width / columns)
            top = round(row * height / rows)
            right = round((column + 1) * width / columns)
            bottom = round((row + 1) * height / rows)

            part = image.crop((left, top, right, bottom))
            data = image_to_bytes(part, "PNG")
            number = row * columns + column + 1

            await send_image(callback.message, data, f"part_{number}.png")

    await callback.answer("Done! Image split.")


# =========================================================
# CONVERT
# =========================================================

@dp.callback_query(F.data == "convert")
async def convert_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="JPG", callback_data="convert_JPEG"),
                InlineKeyboardButton(text="PNG", callback_data="convert_PNG"),
                InlineKeyboardButton(text="WEBP", callback_data="convert_WEBP"),
            ],
            [InlineKeyboardButton(text="◀️ Back", callback_data="back")]
        ]
    )

    await callback.message.answer(
        "🔄 Convert Format\n\nChoose output format:",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("convert_"))
async def convert_image(callback: CallbackQuery):
    user_id = callback.from_user.id
    image = get_image(user_id)

    if image is None:
        await callback.answer("Please send a photo first!", show_alert=True)
        return

    fmt = callback.data.split("_")[1]
    data = image_to_bytes(image, fmt)
    extension = fmt.lower()

    await send_image(callback.message, data, f"converted.{extension}")
    await callback.answer("Done! Format converted.")


# =========================================================
# CROP
# =========================================================

@dp.callback_query(F.data == "crop")
async def crop_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1:1 (Square)", callback_data="crop_1_1"),
                InlineKeyboardButton(text="4:3", callback_data="crop_4_3"),
            ],
            [
                InlineKeyboardButton(text="16:9", callback_data="crop_16_9"),
                InlineKeyboardButton(text="9:16 (Story)", callback_data="crop_9_16"),
            ],
            [InlineKeyboardButton(text="◀️ Back", callback_data="back")]
        ]
    )

    await callback.message.answer(
        "✂️ Crop Image\n\nSelect aspect ratio:",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("crop_"))
async def crop_image(callback: CallbackQuery):
    user_id = callback.from_user.id
    image = get_image(user_id)

    if image is None:
        await callback.answer("Please send a photo first!", show_alert=True)
        return

    _, ratio_w, ratio_h = callback.data.split("_")
    ratio_w, ratio_h = int(ratio_w), int(ratio_h)

    target_ratio = ratio_w / ratio_h
    current_ratio = image.width / image.height

    if current_ratio > target_ratio:
        new_width = int(image.height * target_ratio)
        left = (image.width - new_width) // 2
        box = (left, 0, left + new_width, image.height)
    else:
        new_height = int(image.width / target_ratio)
        top = (image.height - new_height) // 2
        box = (0, top, image.width, top + new_height)

    cropped = image.crop(box)
    data = image_to_bytes(cropped, "PNG")

    await send_image(callback.message, data, f"crop_{ratio_w}x{ratio_h}.png")
    await callback.answer("Done! Image cropped.")


# =========================================================
# REMOVE EXIF & ROTATE
# =========================================================

@dp.callback_query(F.data == "exif")
async def remove_exif(callback: CallbackQuery):
    user_id = callback.from_user.id
    image = get_image(user_id)

    if image is None:
        await callback.answer("Please send a photo first!", show_alert=True)
        return

    data = image_to_bytes(
        image,
        "JPEG" if image.format in ("JPEG", "JPG") else "PNG"
    )

    await send_image(callback.message, data, "clean_image.jpg")
    await callback.answer("Done! Metadata removed.")


@dp.callback_query(F.data == "rotate")
async def rotate_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="90° Clockwise", callback_data="rot_270"),
                InlineKeyboardButton(text="90° Counter-clockwise", callback_data="rot_90"),
            ],
            [InlineKeyboardButton(text="180°", callback_data="rot_180")],
            [InlineKeyboardButton(text="◀️ Back", callback_data="back")]
        ]
    )

    await callback.message.answer(
        "🔄 Rotate Image\n\nChoose rotation angle:",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("rot_"))
async def rotate_image(callback: CallbackQuery):
    user_id = callback.from_user.id
    image = get_image(user_id)

    if image is None:
        await callback.answer("Please send a photo first!", show_alert=True)
        return

    degrees = int(callback.data.split("_")[1])
    rotated = image.rotate(degrees, expand=True)
    data = image_to_bytes(rotated, "PNG")

    await send_image(callback.message, data, "rotated.png")
    await callback.answer("Done! Image rotated.")


# =========================================================
# BACK & UNKNOWN MESSAGES
# =========================================================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.answer(
        "✨ IMGFORCE Main Menu.\n\nSelect an operation:",
        reply_markup=main_keyboard()
    )
    await callback.answer()


@dp.message()
async def unknown_message(message: Message):
    await message.answer(
        "👋 Please send me a photo to start working.",
        reply_markup=main_keyboard()
    )


# =========================================================
# START BOT
# =========================================================

async def main():
    logging.info("IMGFORCE bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    asyncio.run(main())
