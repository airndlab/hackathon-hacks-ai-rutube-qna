import logging
import uuid
from typing import Optional, Dict

import sys
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from app.metrics import set_feedback, init_db, save_answer
from app.service import get_answer

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


class Answer(BaseModel):
    id: str
    answer: str
    class_1: str
    class_2: str
    extra_fields: Optional[Dict[str, str]] = None


@app.post("/api/answers", response_model=Answer)
async def ask(request: QuestionRequest) -> Answer:
    question = request.question
    pipeline = request.pipeline
    answer_data = await get_answer(question, pipeline)
    answer_id = str(uuid.uuid4())
    answer = answer_data.answer
    await save_answer(answer_id, question, answer=answer)
    return Answer(
        id=answer_id,
        answer=answer,
        class_1=answer_data.class_1,
        class_2=answer_data.class_2,
        extra_fields=answer_data.extra_fields
    )


@app.post("/api/answers/{answer_id}/liking")
async def like(answer_id: str) -> None:
    await set_feedback(answer_id, 1)


@app.post("/api/answers/{answer_id}/disliking")
async def dislike(answer_id: str) -> None:
    await set_feedback(answer_id, -1)


@app.on_event("startup")
async def startup_event():
    await init_db()


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8080)
