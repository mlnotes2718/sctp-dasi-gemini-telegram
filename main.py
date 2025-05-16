import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import Bot, Update
from google import genai

# ─── Config ────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
WEBHOOK_URL    = os.getenv("WEBHOOK_URL")  # e.g. https://<your-app>.onrender.com/webhook
MODEL_NAME     = "gemini-2.0-flash"

if not TELEGRAM_TOKEN or not GOOGLE_API_KEY or not WEBHOOK_URL:
    raise RuntimeError("Set TELEGRAM_TOKEN, GOOGLE_API_KEY & WEBHOOK_URL")

# ─── Clients ───────────────────────────────────────────────
bot    = Bot(token=TELEGRAM_TOKEN)
client = genai.Client(api_key=GOOGLE_API_KEY)
logging.basicConfig(level=logging.INFO)

# ─── Lifespan handler replaces on_event("startup") ────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")
    yield
    # shutdown (none needed here)

app = FastAPI(lifespan=lifespan)

# ─── Routes ────────────────────────────────────────────────
@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

@app.head("/")
async def health_head():
    return Response(status_code=200)

@app.get("/")
async def health_get():
    return {"status": "ok"}

@app.post("/webhook")
async def telegram_webhook(req: Request):
    payload = await req.json()
    update  = Update.de_json(payload, bot)

    if update.message and update.message.text:
        user_text = update.message.text
        logging.info(f"User → {user_text!r}")

        resp = client.models.generate_content(
            model=MODEL_NAME,
            contents=[user_text]
        )
        reply = resp.text.strip()
        await bot.send_message(chat_id=update.effective_chat.id, text=reply)

    return {"ok": True}

# ─── Embedded Uvicorn runner ──────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        # note: no reload=True here
    )
