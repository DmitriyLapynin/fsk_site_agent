import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv
import os
import aiohttp

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
FASTAPI_ASSISTANT_URL = os.getenv("ASSISTANT_API_URL", "http://localhost:8000/ask")

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# 📩 Обращение к FastAPI-ассистенту
async def send_to_assistant(user_id: str, message: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(FASTAPI_ASSISTANT_URL, json={"user_id": user_id, "message": message}) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return {"answer": "Ошибка при обращении к ассистенту.", "context": ""}

# 📬 Обработчик сообщений
@dp.message(F.text)
async def handle_message(message: Message):
    user_id = str(message.from_user.id)
    text = message.text

    try:
        response = await send_to_assistant(user_id, text)
        await message.answer(response["answer"])
        logging.info(f"Question: {text}\nAnswer: {response['answer']}\n---\n")
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("Произошла ошибка при обращении к LLM.")