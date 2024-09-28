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

import asyncio
import os
import re
import warnings

import pandas as pd
import pymorphy2
import time
from haystack import Document
from haystack import Pipeline
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.utils import ComponentDevice
from pydantic import BaseModel

warnings.filterwarnings('ignore')

KNOWLEDGE_BASE_FILE_PATH = os.getenv('KNOWLEDGE_BASE_FILE_PATH')

df = pd.read_excel(KNOWLEDGE_BASE_FILE_PATH)
docs = [
    Document(content=row['Вопрос из БЗ'], meta={"url": ""})
    for index, row in df.iterrows()
]

device = ComponentDevice.from_str("cuda:0")
embed_model = "intfloat/e5-large-v2"

doc_embedder = SentenceTransformersDocumentEmbedder(
    model=embed_model,
    device=device
)

doc_embedder.warm_up()
document_store = InMemoryDocumentStore()
docs_with_embeddings = doc_embedder.run(docs)
unique_docs = {doc.id: doc for doc in docs_with_embeddings["documents"]}.values()
document_store.write_documents(list(unique_docs))
text_embedder = SentenceTransformersTextEmbedder(
    model=embed_model,
    device=device
)
retriever = InMemoryEmbeddingRetriever(document_store, top_k=1)
basic_rag_pipeline = Pipeline()
basic_rag_pipeline.add_component("text_embedder", text_embedder)
basic_rag_pipeline.add_component("retriever", retriever)
basic_rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")

replace_dict = {
    'шортс': 'shorts',
    "рутуб": "rutube",
    "рутубе": "rutube",
    "рутуба": "rutube",
    "рутубу": "rutube",
    "ютуб": "youtube",
    "ютубе": "youtube",
    "ютуба": "youtube",
    "ютубу": "youtube",
    "смарт": "smart",
    "тв": "tv",
    "самсунг": "samsung",
    "урл": "url",
}


def get_answer_from_rag(question: str, basic_rag_pipeline, df: pd.DataFrame = df):
    """
    Функция принимает на вход вопрос, приводит его к нижнему регистру, удаляет знаки препинания,
    заменяет слова на основании словаря (если передан), ищет его через RAG pipeline,
    и возвращает соответствующий ответ вместе с классификаторами.

    Параметры:
    - question (str): Вопрос, который передаётся в RAG pipeline.
    - basic_rag_pipeline: RAG pipeline для обработки запроса.
    - replace_dict (dict, optional): Словарь для замены слов в вопросе (например, {'шортс': 'shorts'}).
    - df (pd.DataFrame, optional): DataFrame, содержащий столбцы 'Вопрос из БЗ', 'Ответ из БЗ',
                                    'Классификатор 1 уровня' и 'Классификатор 2 уровня'.

    Возвращает:
    - Tuple[str, str, str]: Ответ из БЗ, классификатор 1 уровня и классификатор 2 уровня.
                             Если ответ не найден, возвращает "Ответ не найден." и пустые строки.
    """
    start_time = time.time()

    morph = pymorphy2.MorphAnalyzer()

    question = question.lower()
    question = re.sub(r'[^\w\s-]', '', question)

    if replace_dict:
        words = question.split()

        replaced_words = []
        for word in words:
            parsed = morph.parse(word)
            if parsed:
                lemma = parsed[0].normal_form
            else:
                lemma = word
            replaced_word = replace_dict.get(lemma, word)
            replaced_words.append(replaced_word)

        question = ' '.join(replaced_words)

    print(f"Processed question: {question}")

    response = basic_rag_pipeline.run({"text_embedder": {"text": question}})

    try:
        target_q = response['retriever']['documents'][0].content
    except (IndexError, KeyError):
        return "Документы не найдены в ответе RAG pipeline.", "", ""

    try:
        target_answer = df.loc[df['Вопрос из БЗ'] == target_q].iloc[0]
        answer_text = target_answer['Ответ из БЗ']
        class_1 = target_answer['Классификатор 1 уровня']
        class_2 = target_answer['Классификатор 2 уровня']

        print(target_answer)

        return answer_text, class_1, class_2
    except IndexError:
        return "Ответ не найден.", "", ""


class Answer(BaseModel):
    answer: str
    class_1: str
    class_2: str


async def get_answer(question: str) -> Answer:
    """
    Асинхронная функция принимает вопрос, получает ответ и классы с помощью RAG pipeline
    и возвращает объект AnswerModel.

    Параметры:
    - question (str): Вопрос, который нужно обработать.
    - basic_rag_pipeline: RAG pipeline для обработки запроса.
    - replace_dict (dict, optional): Словарь для замены слов в вопросе.
    - df (pd.DataFrame, optional): DataFrame, содержащий столбцы 'Вопрос из БЗ', 'Ответ из БЗ',
                                    'Классификатор 1 уровня' и 'Классификатор 2 уровня'.

    Возвращает:
    - AnswerModel: Объект с полями answer, class_1 и class_2.
    """
    loop = asyncio.get_event_loop()
    # Запуск синхронной функции в отдельном потоке, чтобы не блокировать event loop
    answer_text, class_1, class_2 = await loop.run_in_executor(
        None,
        get_answer_from_rag,
        question,
        basic_rag_pipeline,
    )
    return Answer(
        answer=answer_text,
        class_1=class_1 if class_1 else "",
        class_2=class_2 if class_2 else "",
    )
