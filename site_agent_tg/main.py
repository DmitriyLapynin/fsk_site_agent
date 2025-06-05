# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from assistant import RealEstateAssistant
import asyncio
from typing import Dict

app = FastAPI(title="Real Estate Assistant API", version="1.0")

assistant = RealEstateAssistant("data/output.md")

# Хранилище user_id -> thread_id
user_threads: Dict[str, str] = {}

class QuestionRequest(BaseModel):
    user_id: str
    message: str

class AnswerResponse(BaseModel):
    answer: str

@app.on_event("startup")
async def on_start():
    await assistant.init()

@app.post("/ask", response_model=AnswerResponse)
async def ask_question(data: QuestionRequest):

    if data.user_id in user_threads:
        thread_id = user_threads[data.user_id]
    else:
        # Создание нового треда
        thread_id = await assistant.create_thread()
        user_threads[data.user_id] = thread_id

    answer = await assistant.send_message(content=data.message, thread_id=thread_id)
    return AnswerResponse(answer=answer)