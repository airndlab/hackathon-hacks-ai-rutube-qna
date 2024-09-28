#  Copyright 2024 AI RnD Lab
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

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
    handlers=[logging.StreamHandler(sys.stdout)]
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
    answer_data = await get_answer(request.question, request.pipeline)
    answer_id = str(uuid.uuid4())
    await save_answer(
        answer_id=answer_id,
        question=request.question,
        pipeline=request.pipeline,
        answer=answer_data.answer,
        class_1=answer_data.class_1,
        class_2=answer_data.class_2,
    )
    return Answer(
        id=answer_id,
        answer=answer_data.answer,
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
