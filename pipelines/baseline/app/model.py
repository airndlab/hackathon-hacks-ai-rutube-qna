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
import warnings

import pandas as pd
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

warnings.filterwarnings('ignore')

KNOWLEDGE_BASE_FILE_PATH = os.getenv('KNOWLEDGE_BASE_FILE_PATH')

faq = pd.read_excel(KNOWLEDGE_BASE_FILE_PATH)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
faq_embeddings = model.encode(faq['Вопрос из БЗ'].values)


class Answer(BaseModel):
    answer: str
    class_1: str
    class_2: str


async def get_answer(question: str) -> Answer:
    question_embedding = model.encode(question)
    similarities = cos_sim(question_embedding, faq_embeddings)
    answer_data = faq.iloc[similarities.argmax().item()]
    return Answer(
        answer=answer_data['Ответ из БЗ'],
        class_1=answer_data['Классификатор 1 уровня'],
        class_2=answer_data['Классификатор 2 уровня'],
    )
