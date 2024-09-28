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

import os
from typing import Optional, Dict

import aiohttp
from pydantic import BaseModel

PIPELINE_BASELINE_SERVICE_URL = os.getenv('PIPELINE_BASELINE_SERVICE_URL', 'http://pipeline-baseline:8088')
PIPELINE_FAQ_SERVICE_URL = os.getenv('PIPELINE_FAQ_SERVICE_URL', 'http://pipeline-faq:8088')
PIPELINE_FAQ_CASES_SERVICE_URL = os.getenv('PIPELINE_FAQ_CASES_SERVICE_URL', 'http://pipeline-faq-cases:8088')

default_pipeline = os.getenv('QNA_SERVICE_DEFAULT_PIPELINE', 'faq_cases')
pipelines = {
    "baseline": "Вариант кейсхолдера",
    "faq": "Поиск по вопросам FAQ",
    "faq_cases": "Поиск по вопросам FAQ+Кейсы"
}


class PipelineAnswer(BaseModel):
    answer: str
    class_1: str
    class_2: str
    extra_fields: Optional[Dict[str, str]] = None


async def get_answer(question: str, pipeline: Optional[str]) -> PipelineAnswer:
    pipeline = pipeline or default_pipeline
    match pipeline:
        case "baseline":
            return await get_answer_by_service(question, PIPELINE_BASELINE_SERVICE_URL)
        case "faq":
            return await get_answer_by_service(question, PIPELINE_FAQ_SERVICE_URL)
        case "faq_cases":
            return await get_answer_by_service(question, PIPELINE_FAQ_CASES_SERVICE_URL)
        case _:
            raise Exception(f'Неизвестный пайплайн: {pipeline}')


async def get_answer_by_service(question: str, service_url: str) -> PipelineAnswer:
    async with aiohttp.ClientSession() as session:
        request = {'question': question}
        async with session.post(f'{service_url}/api/answers', json=request) as response:
            if response.status == 200:
                json = await response.json()
                return PipelineAnswer(**json)
            else:
                raise Exception(f"Ошибка получения ответа: {response.status} {response.text()}")
