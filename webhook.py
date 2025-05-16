# main.py
import os
import logging

from fastapi import FastAPI, Request
from telegram import Bot, Update
import openai

# --- Configuration from environment ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://<your-app>.onrender.com/webhook

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise RuntimeError("Set TELEGRAM_TOKEN, OPENAI_API_KEY & WEBHOOK_URL")

# --- Clients ---
bot = Bot(token=TELEGRAM_TOKEN)
openai.api_key = OPENAI_API_KEY

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

        # Call OpenAI asynchronously
        resp = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_text}],
        )
        reply = resp.choices[0].message.content.strip()

        await bot.send_message(chat_id=update.effective_chat.id, text=reply)

    return {"ok": True}


@app.get("/")
async def health_check():
    return {"status": "ok"}
