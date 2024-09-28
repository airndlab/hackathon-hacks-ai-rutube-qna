import logging
from typing import Optional

import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from app.service import get_answer, Answer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

app = FastAPI()


@app.get("/")
async def root():
    return {"status": "UP"}


class QuestionRequest(BaseModel):
    question: str
    pipeline: Optional[str] = None


@app.post("/api/answers", response_model=Answer)
async def ask(request: QuestionRequest) -> Answer:
    question = request.question
    pipeline = request.pipeline
    return await get_answer(question, pipeline)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080)
