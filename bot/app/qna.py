import os

import aiohttp
from pydantic import BaseModel

QNA_SERVICE_URL = os.getenv('QNA_SERVICE_URL', 'http://qna-service:8080')


class Answer(BaseModel):
    answer: str
    class_1: str
    class_2: str


async def get_answer(question: str) -> Answer:
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{QNA_SERVICE_URL}/api/answers', json={
            'question': question
        }) as response:
            if response.status == 200:
                json = await response.json()
                return Answer(**json)
            else:
                raise Exception(f"Ошибка получения ответа: {response.status} {response.text()}")
