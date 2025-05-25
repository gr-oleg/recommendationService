import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import openai

ITEM_SERVICE_URL = "http://16.171.137.58/item/getAll"

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не знайдено в .env файлі!")

client = openai.OpenAI(api_key=OPENAI_API_KEY)
app = FastAPI()

# Дозволити CORS (для роботи з фронтендом)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = (
    "Ти — AI-консультант інтернет-магазину. "
    "Відповідай українською, допомагай у виборі товарів, пояснюй акції, допомагай із замовленням."
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

def fetch_items():
    try:
        resp = requests.get(ITEM_SERVICE_URL, timeout=5)
        resp.raise_for_status()
        items = resp.json()
        # Можна адаптувати під свою структуру відповіді!
        item_lines = []
        for item in items:
            item_lines.append(f"{item.get('name')}: {item.get('description', '')} (ціна: {item.get('price', '')})")
        items_str = "\n".join(item_lines)
        return items_str
    except Exception as e:
        return "Наразі перелік товарів недоступний."

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        # Підтягуємо список товарів
        item_info = fetch_items()
        # Додаємо це до system prompt або assistant context
        system_message = {
            "role": "system",
            "content": SYSTEM_PROMPT + "\nОсь актуальний перелік товарів:\n" + item_info
        }
        all_messages = [system_message] + [m.dict() for m in req.messages]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=all_messages,
            max_tokens=400,
            temperature=0.7,
        )
        answer = response.choices[0].message.content.strip()
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})