import os
import logging
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import replicate
import uuid
import requests
from datetime import datetime

load_dotenv()

# ENV Vars
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")
OWNER_USERNAME = os.getenv("OWNER_USERNAME")

# Init
app = Client("cartoon_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
replicate.Client(api_token=REPLICATE_API_KEY)
logging.basicConfig(level=logging.INFO)

# Styles
STYLES = {
    "Ghibli": "prompthero/openjourney",
    "Pixar": "fofr/anything-v4.0",
    "Sketch": "stability-ai/stable-diffusion",
    "Realistic": "stability-ai/stable-diffusion"
}

# In-memory user data (reset every run)
user_sessions = {}

# Log file
LOG_FILE = "logs.txt"

def log_action(user_id, action):
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now()} | {user_id} | {action}\n")


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    user_sessions[message.from_user.id] = {}
    await message.reply(
        f"👋 Hello {message.from_user.first_name}!\nChoose your style:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(style, callback_data=f"style:{style}")] for style in STYLES
        ])
    )
    log_action(message.from_user.id, "Started bot")


@app.on_callback_query(filters.regex("^style:"))
async def style_selected(client, callback_query):
    style = callback_query.data.split(":")[1]
    user_sessions[callback_query.from_user.id]["style"] = style
    await callback_query.message.reply("📷 Send a photo to convert!")
    await callback_query.answer(f"Style set to {style}")
    log_action(callback_query.from_user.id, f"Selected style: {style}")


@app.on_message(filters.photo)
async def handle_photo(client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_sessions or "style" not in user_sessions[user_id]:
        await message.reply("❗ Please /start and select a style first.")
        return

    style = user_sessions[user_id]["style"]
    file_path = await message.download()
    await message.reply("🧠 AI is processing your image...")

    output_url = run_ai(file_path, style)
    if output_url:
        await message.reply_photo(photo=output_url, caption=f"✨ Style: {style}")
        log_action(user_id, f"Converted image using {style}")
    else:
        await message.reply("⚠️ Failed to generate image.")
        log_action(user_id, "Image generation failed")


def run_ai(image_path, style):
    try:
        with open(image_path, "rb") as file:
            img_upload = replicate.files.upload(file)
        output = replicate.run(
            STYLES[style] + ":latest",
            input={"image": img_upload}
        )
        return output[0] if output else None
    except Exception as e:
        print("Error:", e)
        return None


@app.on_message(filters.command("vip"))
async def vip_info(client, message: Message):
    await message.reply(
        "💎 VIP Access costs ₹99. UPI QR below. After payment, forward receipt to @" + OWNER_USERNAME,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Pay Now", url="upi://pay?pa=yourupi@upi&pn=CartoonBot&am=99")]
        ])
    )
    log_action(message.from_user.id, "Requested VIP info")


@app.on_message(filters.command("log"))
async def show_logs(client, message: Message):
    if message.from_user.username != OWNER_USERNAME:
        return await message.reply("Access Denied ❌")

    with open(LOG_FILE, "rb") as f:
        await message.reply_document(f)


app.run()
