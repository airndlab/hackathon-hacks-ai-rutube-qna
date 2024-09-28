import os
from typing import Optional

import aiohttp
from pydantic import BaseModel

PIPELINE_BASELINE_SERVICE_URL = os.getenv('PIPELINE_BASELINE_SERVICE_URL', 'http://pipeline-baseline:8088')
PIPELINE_FAQ_SERVICE_URL = os.getenv('PIPELINE_FAQ_SERVICE_URL', 'http://pipeline-faq:8088')
PIPELINE_FAQ_CASES_SERVICE_URL = os.getenv('PIPELINE_FAQ_CASES_SERVICE_URL', 'http://pipeline-faq-cases:8088')

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


async def get_answer(question: str, pipeline: Optional[str] = default_pipeline) -> Answer:
    match pipeline:
        case "baseline":
            return await get_answer_by_service(question, PIPELINE_BASELINE_SERVICE_URL)
        case "faq":
            return await get_answer_by_service(question, PIPELINE_FAQ_SERVICE_URL)
        case "faq_cases":
            return await get_answer_by_service(question, PIPELINE_FAQ_CASES_SERVICE_URL)
        case _:
            raise Exception(f'Неизвестный пайплайн: {pipeline}')


async def get_answer_by_service(question: str, service_url: str) -> Answer:
    async with aiohttp.ClientSession() as session:
        request = {'question': question}
        async with session.post(f'{service_url}/api/answers', json=request) as response:
            if response.status == 200:
                json = await response.json()
                return Answer(**json)
            else:
                raise Exception(f"Ошибка получения ответа: {response.status} {response.text()}")
