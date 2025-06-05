import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
import json
import openai

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

class RealEstateAssistant:
    def __init__(self, path_file: str):
        self.api_key = OPENAI_API_KEY
        self.model_name = MODEL_NAME
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.path_file = path_file
        self.assistant = None

    async def init(self):
        file = self.client.files.create(
            file=open(self.path_file, "rb"),
            purpose="assistants"
        )
        
        vector_store = self.client.vector_stores.create(
              name="lka",
              file_ids=[file.id]
            )
        
        instructions = self.get_system_prompt()
        
        self.assistant = self.client.beta.assistants.create(
            name="lka",
            instructions=instructions,
            model=self.model_name,
            tools=[{"type": "file_search"}],
            tool_resources={
            "file_search": {
            "vector_store_ids": [vector_store.id]
            }
        }
        )

    async def create_thread(self) -> str:
        thread = self.client.beta.threads.create()
        return thread.id
    
    async def delete_thread(self, thread_id: str):
        self.client.beta.threads.delete(thread_id)

    def get_system_prompt(self) -> str:
        with open("system_prompt.txt", "r", encoding="utf-8") as f:
            instructions = f.read()
        return instructions

    async def send_message(self,
                           content: str, 
                           thread_id: str, 
                          ) -> str:
        message = self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content
        )
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
        )
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
        )
            if run_status.status in ["completed", "failed"]:
                break
            await asyncio.sleep(1)
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        latest_message = messages.data[0]
        
        return latest_message.content[0].text.value


    async def get_messages(self, thread_id: str, before: str = None) -> list[str]:
        messages = self.client.beta.threads.messages.list(thread_id=thread_id, before=before)
        try:
            result = []
            response = [json.loads(message.content[0].text.value)['response'] for message in messages.data[::-1]]
            for answer in response:
                result.extend(answer.split("\n\n"))
            return result
        except:
            response = [message.content[0].text.value for message in messages.data[::-1]]
            for answer in response:
                result.extend(answer.split("\n\n"))
            return result