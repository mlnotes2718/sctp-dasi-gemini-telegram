# main.py
import os
import logging

from fastapi import FastAPI, Request
from telegram import Bot, Update
from google import genai


# --- Configuration from environment ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://<your-app>.onrender.com/webhook
MODEL_NAME  = "gemini-2.0-flash"

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY or not WEBHOOK_URL:
    raise RuntimeError("Set TELEGRAM_TOKEN, GOOGLE_API_KEY & WEBHOOK_URL")

# --- Clients ---
bot = Bot(token=TELEGRAM_TOKEN)
gemini_api_key = GOOGLE_API_KEY
client = genai.Client(api_key=gemini_api_key)

app = FastAPI()
logging.basicConfig(level=logging.INFO)


@app.on_event("startup")
async def startup():
    # (Re)register webhook so Telegram knows where to POST updates
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("Webhook set to %s", WEBHOOK_URL)


@app.post("/webhook")
async def telegram_webhook(req: Request):
    body = await req.json()
    update = Update.de_json(body, bot)

    if update.message and update.message.text:
        user_text = update.message.text
        logging.info("User wrote: %s", user_text)

        # Query Gemini
        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=[user_text]
        )
        reply = resp.text.strip()

        await bot.send_message(chat_id=update.effective_chat.id, text=reply)

    return {"ok": True}


@app.get("/")
async def health_check():
    return {"status": "ok"}
