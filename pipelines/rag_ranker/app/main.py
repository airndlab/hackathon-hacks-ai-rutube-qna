import logging
import sys

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from app.model import get_answer, Answer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

app = FastAPI()


@app.get("/")
def index():
    return {"text": "Интеллектуальный помощник оператора службы поддержки."}


class QuestionRequest(BaseModel):
    question: str


@app.post("/api/answers", response_model=Answer)
async def ask(request: QuestionRequest) -> Answer:
    return await get_answer(request.question)


@app.post("/predict")
async def predict(request: QuestionRequest) -> Answer:
    return await get_answer(request.question)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8083)
