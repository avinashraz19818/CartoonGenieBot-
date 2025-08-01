import os
import replicate
from pyrogram import Client, filters
from pyrogram.types import Message
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY")
OWNER_USERNAME = os.getenv("OWNER_USERNAME")

# Set up Replicate
replicate_client = replicate.Client(api_token=REPLICATE_API_KEY)

# Initialize the bot
app = Client("ai_cartoon_bot", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH)

# In-memory user limits
user_limits = {}

@app.on_message(filters.command("start"))
async def start(client, message: Message):
    await message.reply_text(
        f"👋 **Welcome to AI Cartoon Bot!**\n\n"
        f"🎨 Send me a photo and I will turn it into a Ghibli-style cartoon image!\n"
        f"💡 Free users can generate 1 image per day.\n\n"
        f"💎 Want unlimited access? Type `/vip`.\n\n"
        f"🔧 Made by @{OWNER_USERNAME}"
    )

@app.on_message(filters.command("vip"))
async def vip(client, message: Message):
    await message.reply_text(
        "**💎 VIP Plan**\n\n"
        "➡ Unlimited cartoon photo generation\n"
        "➡ Price: ₹49/month\n"
        "➡ Pay via UPI: `yourupi@bank`\n"
        "📩 After payment, send proof to: @" + OWNER_USERNAME
    )

@app.on_message(filters.photo)
async def handle_photo(client, message: Message):
    user_id = message.from_user.id

    # Limit check
    if user_limits.get(user_id, 0) >= 1:
        await message.reply_text("❌ Free limit reached. Type /vip to unlock unlimited use.")
        return

    file_path = await message.download()
    await message.reply_text("🎨 Converting your photo to cartoon style... Please wait...")

    try:
        output = replicate_client.run(
            "fofr/anything-to-ghibli:15f086f3cd12e44271939f1d2b0fa8bd3019d4c016238d8e7b1efba1d1c6b75c",
            input={"image": open(file_path, "rb")}
        )
        cartoon_url = output["output"]
        await message.reply_photo(cartoon_url, caption="Here is your cartoon image! 😊")
        user_limits[user_id] = user_limits.get(user_id, 0) + 1
    except Exception as e:
        await message.reply_text(f"❌ Failed to generate image. Error: {e}")
    finally:
        os.remove(file_path)

app.run()
