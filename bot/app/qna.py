import os
from typing import Optional

import aiohttp
from pydantic import BaseModel

QNA_SERVICE_URL = os.getenv('QNA_SERVICE_URL', 'http://qna-service:8080')

default_pipeline = 'baseline'
pipelines = {
    "baseline": "Вариант кейсхолдера",
    "faq": "Поиск по вопросам FAQ",
    "faq_cases": "Поиск по вопросам FAQ+Кейсы"
}


class Answer(BaseModel):
    answer: str
    class_1: str
    class_2: str


async def get_answer(question: str, pipeline: Optional[str] = None) -> Answer:
    async with aiohttp.ClientSession() as session:
        request = {'question': question}
        if pipeline:
            request['pipeline'] = pipeline
        async with session.post(f'{QNA_SERVICE_URL}/api/answers', json=request) as response:
            if response.status == 200:
                json = await response.json()
                return Answer(**json)
            else:
                raise Exception(f"Ошибка получения ответа: {response.status} {response.text()}")
