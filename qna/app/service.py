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

QNA_SERVICE_DEFAULT_PIPELINE = os.getenv('QNA_SERVICE_DEFAULT_PIPELINE', 'faq_cases')

SERVICE_URLS = {
    "baseline": os.getenv('PIPELINE_BASELINE_SERVICE_URL', 'http://pipeline-baseline:8088'),
    "faq": os.getenv('PIPELINE_FAQ_SERVICE_URL', 'http://pipeline-faq:8088'),
    "faq_cases": os.getenv('PIPELINE_FAQ_CASES_SERVICE_URL', 'http://pipeline-faq-cases:8088'),
}


class PipelineAnswer(BaseModel):
    answer: str
    class_1: str
    class_2: str
    extra_fields: Optional[Dict[str, str]] = None


# Получить ответ у пайплайна
async def get_answer(question: str, pipeline: Optional[str] = None) -> PipelineAnswer:
    pipeline = pipeline or QNA_SERVICE_DEFAULT_PIPELINE
    if pipeline not in SERVICE_URLS:
        raise ValueError(f'Неизвестный пайплайн: {pipeline}')

    service_url = SERVICE_URLS[pipeline]
    return await get_answer_by_service(question, service_url)


# Запросить ответ у пайплайн сервиса
async def get_answer_by_service(question: str, service_url: str) -> PipelineAnswer:
    async with aiohttp.ClientSession() as session:
        request = {'question': question}
        async with session.post(f'{service_url}/api/answers', json=request) as response:
            if response.status != 200:
                raise Exception(f"Ошибка получения ответа: {response.status} {await response.text()}")
            return PipelineAnswer(**await response.json())
