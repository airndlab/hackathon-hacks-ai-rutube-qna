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

# Отключение предупреждений
warnings.filterwarnings('ignore')

# Путь к файлу базы знаний из переменной окружения
KNOWLEDGE_BASE_FILE_PATH = os.getenv('KNOWLEDGE_BASE_FILE_PATH')

# Загрузка данных из Excel в DataFrame
faq = pd.read_excel(KNOWLEDGE_BASE_FILE_PATH)

# Инициализация модели SentenceTransformer для векторного представления текстов
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Кодирование вопросов из базы знаний в векторы
faq_embeddings = model.encode(faq['Вопрос из БЗ'].values)


# Модель ответа с полями ответа и классификаторами
class Answer(BaseModel):
    answer: str
    class_1: str
    class_2: str


# Функция для получения ответа на вопрос
async def get_answer(question: str) -> Answer:
    # Кодирование заданного вопроса в вектор
    question_embedding = model.encode(question)

    # Вычисление косинусного сходства между вопросом и всеми вопросами из БЗ
    similarities = cos_sim(question_embedding, faq_embeddings)

    # Получение наиболее похожего ответа по индексу максимального значения сходства
    answer_data = faq.iloc[similarities.argmax().item()]

    # Формирование объекта ответа с данными из базы
    return Answer(
        answer=answer_data['Ответ из БЗ'],
        class_1=answer_data['Классификатор 1 уровня'],
        class_2=answer_data['Классификатор 2 уровня'],
    )
