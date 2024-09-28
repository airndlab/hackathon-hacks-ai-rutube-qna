import os
from typing import Optional, Dict

import aiohttp
from pydantic import BaseModel

QNA_SERVICE_URL = os.getenv('QNA_SERVICE_URL', 'http://qna-service:8080')


class Answer(BaseModel):
    id: str
    answer: str
    class_1: str
    class_2: str
    extra_fields: Optional[Dict[str, str]] = None

    def get_other_inline(self) -> Optional[str]:
        if self.extra_fields:
            return ' '.join(f'{k} {v}' for k, v in self.extra_fields.items())
        return None


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


async def like_answer(answer_id: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{QNA_SERVICE_URL}/api/answers/{answer_id}/liking') as response:
            if response.status != 200:
                raise Exception(f"Ошибка положительной оценки ответа '{answer_id}'"
                                f": {response.status} {response.text()}")


async def dislike_answer(answer_id: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.post(f'{QNA_SERVICE_URL}/api/answers/{answer_id}/disliking') as response:
            if response.status != 200:
                raise Exception(f"Ошибка отрицательной оценки ответа '{answer_id}'"
                                f": {response.status} {response.text()}")
