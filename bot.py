import asyncio
import io
import logging
import os
import math

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    BufferedInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from PIL import Image, ImageOps, ExifTags


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")


logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

# user_id -> original image bytes
images = {}


# =========================
# KEYBOARDS
# =========================

def main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🗜 Compress",
                    callback_data="compress"
                ),
                InlineKeyboardButton(
                    text="📐 Resize",
                    callback_data="resize"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="✂️ Split",
                    callback_data="split"
                ),
                InlineKeyboardButton(
                    text="🔄 Convert",
                    callback_data="convert"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🖼 Crop",
                    callback_data="crop"
                ),
                InlineKeyboardButton(
                    text="ℹ️ Image info",
                    callback_data="info"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🧹 Remove EXIF",
                    callback_data="exif"
                ),
                InlineKeyboardButton(
                    text="🔃 Rotate",
                    callback_data="rotate"
                ),
            ],
        ]
    )


def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back"
                )
            ]
        ]
    )


# =========================
# HELPERS
# =========================

def get_image(user_id: int):
    if user_id not in images:
        return None

    return Image.open(io.BytesIO(images[user_id]))


def image_to_bytes(image: Image.Image, fmt="PNG", quality=90):
    output = io.BytesIO()

    if fmt.upper() in ("JPG", "JPEG"):
        if image.mode not in ("RGB", "L"):
            background = Image.new("RGB", image.size, "white")

            if "A" in image.getbands():
                background.paste(
                    image,
                    mask=image.getchannel("A")
                )
            else:
                background.paste(image)

            image = background

        image.save(
            output,
            format="JPEG",
            quality=quality,
            optimize=True
        )

    elif fmt.upper() == "WEBP":
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")

        image.save(
            output,
            format="WEBP",
            quality=quality,
            method=6
        )

    else:
        image.save(output, format=fmt)

    output.seek(0)
    return output.read()


async def send_image(
    message: Message,
    data: bytes,
    filename: str
):
    await message.answer_document(
        BufferedInputFile(
            data,
            filename=filename
        )
    )


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "<b>🖼 IMGFORCE</b>\n\n"
        "Image processing toolkit for Telegram.\n\n"
        "Send me a photo and choose what you want to do with it.",
        reply_markup=main_keyboard()
    )


@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "<b>IMGFORCE</b>\n\n"
        "Available tools:\n\n"
        "🗜 Compress — reduce file size\n"
        "📐 Resize — change resolution\n"
        "✂️ Split — divide image into parts\n"
        "🔄 Convert — JPG / PNG / WEBP\n"
        "🖼 Crop — crop by aspect ratio\n"
        "ℹ️ Image info — technical information\n"
        "🧹 Remove EXIF — remove metadata\n"
        "🔃 Rotate — rotate image\n\n"
        "Just send a photo to begin."
    )


# =========================
# RECEIVE IMAGE
# =========================

@dp.message(F.photo)
async def receive_photo(message: Message):
    photo = message.photo[-1]

    file = await bot.get_file(photo.file_id)

    data = await bot.download_file(
        file.file_path
    )

    images[message.from_user.id] = data.getvalue()

    image = get_image(message.from_user.id)

    await message.answer(
        f"✅ <b>Image received</b>\n\n"
        f"Resolution: <code>{image.width}×{image.height}</code>\n"
        f"Format: <code>{image.format}</code>\n\n"
        f"Choose an operation:",
        reply_markup=main_keyboard()
    )


# =========================
# INFO
# =========================

@dp.callback_query(F.data == "info")
async def image_info(callback: CallbackQuery):
    image = get_image(callback.from_user.id)

    if image is None:
        await callback.answer(
            "Send an image first.",
            show_alert=True
        )
        return

    size_kb = len(
        images[callback.from_user.id]
    ) / 1024

    await callback.message.answer(
        "<b>ℹ️ Image information</b>\n\n"
        f"Format: <code>{image.format}</code>\n"
        f"Resolution: <code>{image.width}×{image.height}</code>\n"
        f"Mode: <code>{image.mode}</code>\n"
        f"File size: <code>{size_kb:.2f} KB</code>\n"
        f"Aspect ratio: <code>{image.width / image.height:.2f}</code>"
    )

    await callback.answer()


# =========================
# COMPRESS
# =========================

@dp.callback_query(F.data == "compress")
async def compress_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔹 80%",
                    callback_data="compress_80"
                ),
                InlineKeyboardButton(
                    text="🔸 60%",
                    callback_data="compress_60"
                ),
                InlineKeyboardButton(
                    text="🔻 40%",
                    callback_data="compress_40"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back"
                )
            ]
        ]
    )

    await callback.message.answer(
        "🗜 <b>Compress</b>\n\n"
        "Choose JPEG quality:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("compress_"))
async def compress_image(callback: CallbackQuery):
    image = get_image(callback.from_user.id)

    if image is None:
        await callback.answer(
            "Send an image first.",
            show_alert=True
        )
        return

    quality = int(
        callback.data.split("_")[1]
    )

    data = image_to_bytes(
        image,
        "JPEG",
        quality
    )

    await send_image(
        callback.message,
        data,
        f"compressed_{quality}.jpg"
    )

    await callback.answer("Done!")


# =========================
# RESIZE
# =========================

@dp.callback_query(F.data == "resize")
async def resize_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1920 px",
                    callback_data="resize_1920"
                ),
                InlineKeyboardButton(
                    text="1280 px",
                    callback_data="resize_1280"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="720 px",
                    callback_data="resize_720"
                ),
                InlineKeyboardButton(
                    text="500 px",
                    callback_data="resize_500"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back"
                )
            ]
        ]
    )

    await callback.message.answer(
        "📐 <b>Resize</b>\n\n"
        "Choose maximum width:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("resize_"))
async def resize_image(callback: CallbackQuery):
    image = get_image(callback.from_user.id)

    if image is None:
        await callback.answer(
            "Send an image first.",
            show_alert=True
        )
        return

    max_width = int(
        callback.data.split("_")[1]
    )

    if image.width > max_width:
        ratio = max_width / image.width

        new_size = (
            max_width,
            int(image.height * ratio)
        )

        image = image.resize(
            new_size,
            Image.Resampling.LANCZOS
        )

    data = image_to_bytes(
        image,
        "PNG"
    )

    await send_image(
        callback.message,
        data,
        f"resized_{image.width}x{image.height}.png"
    )

    await callback.answer("Done!")


# =========================
# SPLIT
# =========================

@dp.callback_query(F.data == "split")
async def split_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="2️⃣ 2 parts",
                    callback_data="split_2"
                ),
                InlineKeyboardButton(
                    text="3️⃣ 3 parts",
                    callback_data="split_3"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="4️⃣ 4 parts",
                    callback_data="split_4"
                ),
                InlineKeyboardButton(
                    text="6️⃣ 6 parts",
                    callback_data="split_6"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="9️⃣ 9 parts",
                    callback_data="split_9"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back"
                )
            ]
        ]
    )

    await callback.message.answer(
        "✂️ <b>Split image</b>\n\n"
        "Choose number of equal parts:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("split_"))
async def split_image(callback: CallbackQuery):
    image = get_image(callback.from_user.id)

    if image is None:
        await callback.answer(
            "Send an image first.",
            show_alert=True
        )
        return

    count = int(
        callback.data.split("_")[1]
    )

    # 2 and 3 = vertical parts
    if count in (2, 3):
        columns = count
        rows = 1

    # 4 = 2x2
    elif count == 4:
        columns = 2
        rows = 2

    # 6 = 3x2
    elif count == 6:
        columns = 3
        rows = 2

    # 9 = 3x3
    else:
        columns = 3
        rows = 3

    width, height = image.size

    for row in range(rows):
        for column in range(columns):

            left = round(
                column * width / columns
            )
            top = round(
                row * height / rows
            )

            right = round(
                (column + 1) * width / columns
            )
            bottom = round(
                (row + 1) * height / rows
            )

            part = image.crop(
                (left, top, right, bottom)
            )

            data = image_to_bytes(
                part,
                "PNG"
            )

            number = (
                row * columns
                + column
                + 1
            )

            await send_image(
                callback.message,
                data,
                f"part_{number}.png"
            )

    await callback.answer("Image split successfully!")


# =========================
# CONVERT
# =========================

@dp.callback_query(F.data == "convert")
async def convert_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="JPG",
                    callback_data="convert_JPEG"
                ),
                InlineKeyboardButton(
                    text="PNG",
                    callback_data="convert_PNG"
                ),
                InlineKeyboardButton(
                    text="WEBP",
                    callback_data="convert_WEBP"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back"
                )
            ]
        ]
    )

    await callback.message.answer(
        "🔄 <b>Convert</b>\n\n"
        "Choose output format:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("convert_"))
async def convert_image(callback: CallbackQuery):
    image = get_image(callback.from_user.id)

    if image is None:
        await callback.answer(
            "Send an image first.",
            show_alert=True
        )
        return

    fmt = callback.data.split("_")[1]

    data = image_to_bytes(
        image,
        fmt
    )

    extension = fmt.lower()

    await send_image(
        callback.message,
        data,
        f"converted.{extension}"
    )

    await callback.answer("Converted!")


# =========================
# CROP
# =========================

@dp.callback_query(F.data == "crop")
async def crop_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="1:1",
                    callback_data="crop_1_1"
                ),
                InlineKeyboardButton(
                    text="4:3",
                    callback_data="crop_4_3"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="16:9",
                    callback_data="crop_16_9"
                ),
                InlineKeyboardButton(
                    text="9:16",
                    callback_data="crop_9_16"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back"
                )
            ]
        ]
    )

    await callback.message.answer(
        "🖼 <b>Crop</b>\n\n"
        "Choose aspect ratio:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("crop_"))
async def crop_image(callback: CallbackQuery):
    image = get_image(callback.from_user.id)

    if image is None:
        await callback.answer(
            "Send an image first.",
            show_alert=True
        )
        return

    _, ratio_w, ratio_h = callback.data.split("_")

    ratio_w = int(ratio_w)
    ratio_h = int(ratio_h)

    target_ratio = ratio_w / ratio_h
    current_ratio = image.width / image.height

    if current_ratio > target_ratio:
        # Too wide
        new_width = int(
            image.height * target_ratio
        )

        left = (image.width - new_width) // 2

        box = (
            left,
            0,
            left + new_width,
            image.height
        )

    else:
        # Too tall
        new_height = int(
            image.width / target_ratio
        )

        top = (image.height - new_height) // 2

        box = (
            0,
            top,
            image.width,
            top + new_height
        )

    cropped = image.crop(box)

    data = image_to_bytes(
        cropped,
        "PNG"
    )

    await send_image(
        callback.message,
        data,
        f"crop_{ratio_w}x{ratio_h}.png"
    )

    await callback.answer("Cropped!")


# =========================
# REMOVE EXIF
# =========================

@dp.callback_query(F.data == "exif")
async def remove_exif(callback: CallbackQuery):
    image = get_image(callback.from_user.id)

    if image is None:
        await callback.answer(
            "Send an image first.",
            show_alert=True
        )
        return

    clean = Image.new(
        image.mode,
        image.size
    )

    clean.putdata(
        list(image.getdata())
    )

    data = image_to_bytes(
        clean,
        "PNG"
    )

    await send_image(
        callback.message,
        data,
        "clean_image.png"
    )

    await callback.answer(
        "Metadata removed!"
    )


# =========================
# ROTATE
# =========================

@dp.callback_query(F.data == "rotate")
async def rotate_menu(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↶ 90°",
                    callback_data="rotate_90"
                ),
                InlineKeyboardButton(
                    text="↷ 270°",
                    callback_data="rotate_270"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔄 180°",
                    callback_data="rotate_180"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Back",
                    callback_data="back"
                )
            ]
        ]
    )

    await callback.message.answer(
        "🔃 <b>Rotate</b>\n\n"
        "Choose rotation:",
        reply_markup=keyboard
    )

    await callback.answer()


@dp.callback_query(F.data.startswith("rotate_"))
async def rotate_image(callback: CallbackQuery):
    image = get_image(callback.from_user.id)

    if image is None:
        await callback.answer(
            "Send an image first.",
            show_alert=True
        )
        return

    degrees = int(
        callback.data.split("_")[1]
    )

    rotated = image.rotate(
        degrees,
        expand=True
    )

    data = image_to_bytes(
        rotated,
        "PNG"
    )

    await send_image(
        callback.message,
        data,
        f"rotated_{degrees}.png"
    )

    await callback.answer("Rotated!")


# =========================
# BACK
# =========================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.answer(
        "🖼 <b>IMGFORCE</b>\n\n"
        "Choose an operation:",
        reply_markup=main_keyboard()
    )

    await callback.answer()


# =========================
# UNKNOWN TEXT
# =========================

@dp.message()
async def unknown_message(message: Message):
    await message.answer(
        "🖼 Send me an image to start.",
        reply_markup=main_keyboard()
    )


# =========================
# RUN
# =========================

async def main():
    logging.info("IMGFORCE started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
