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
async def root():
    return {"status": "UP"}


class QuestionRequest(BaseModel):
    question: str


@app.post("/api/answers", response_model=Answer)
async def ask(request: QuestionRequest) -> Answer:
    return await get_answer(request.question)


if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8088)
