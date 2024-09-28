import asyncio
import json
import os
import re
import warnings

import pandas as pd
import pymorphy2
from haystack import Document, Pipeline
from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.utils import ComponentDevice
from pydantic import BaseModel

NO_ANSWER = "Ответ не найден."

# Отключение предупреждений
warnings.filterwarnings('ignore')

# Путь к файлу базы знаний из переменной окружения
KNOWLEDGE_BASE_FILE_PATH = os.getenv('KNOWLEDGE_BASE_FILE_PATH')

# Загрузка базы знаний
df = pd.read_excel(KNOWLEDGE_BASE_FILE_PATH)
# Преобразование данных из DataFrame в список документов
docs = [Document(content=row['Вопрос из БЗ'], meta={"url": ""}) for _, row in df.iterrows()]

# Настройка устройства и модели для эмбеддинга
device = ComponentDevice.from_str("cuda:0")
embed_model = "intfloat/e5-large-v2"

# Инициализация эмбеддера для документов
doc_embedder = SentenceTransformersDocumentEmbedder(model=embed_model, device=device)
doc_embedder.warm_up()  # Прогрев модели

# Инициализация хранилища документов
document_store = InMemoryDocumentStore()
docs_with_embeddings = doc_embedder.run(docs)
unique_docs = {doc.id: doc for doc in docs_with_embeddings["documents"]}.values()
document_store.write_documents(list(unique_docs))

# Настройка эмбеддера текста и извлекателя
text_embedder = SentenceTransformersTextEmbedder(model=embed_model, device=device)
retriever = InMemoryEmbeddingRetriever(document_store, top_k=1)

# Создание и настройка RAG pipeline
basic_rag_pipeline = Pipeline()
basic_rag_pipeline.add_component("text_embedder", text_embedder)
basic_rag_pipeline.add_component("retriever", retriever)
basic_rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")

# Загрузка замен слов на их эквиваленты из файла
REPLACEMENTS_FILE_PATH = os.getenv('REPLACEMENTS_FILE_PATH')
with open(REPLACEMENTS_FILE_PATH, 'r', encoding='utf-8') as file:
    replace_dict = json.load(file)


def get_answer_from_rag(question: str, rag_pipeline, dataframe: pd.DataFrame = df):
    """
    Обрабатывает вопрос, приводит его к нормализованной форме, заменяет слова и ищет ответ в RAG pipeline.

    Параметры:
    - question (str): Вопрос для поиска.
    - basic_rag_pipeline: RAG pipeline для поиска.
    - df (pd.DataFrame, optional): DataFrame с базой знаний.

    Возвращает:
    - Tuple[str, str, str]: Ответ и классификаторы. Если ответ не найден, возвращает "Ответ не найден." и пустые строки.
    """
    morph = pymorphy2.MorphAnalyzer()

    # Преобразование вопроса к нижнему регистру и удаление знаков препинания
    question = re.sub(r'[^\w\s-]', '', question.lower())

    # Замена слов на основании словаря
    words = question.split()
    replaced_words = [replace_dict.get(morph.parse(word)[0].normal_form, word) for word in words]
    question = ' '.join(replaced_words)

    # Запуск поиска в RAG pipeline
    response = rag_pipeline.run({"text_embedder": {"text": question}})

    try:
        # Получение текста вопроса из RAG pipeline
        target_q = response['retriever']['documents'][0].content
    except (IndexError, KeyError):
        return "Документы не найдены в ответе RAG pipeline.", "", ""

    try:
        # Поиск ответа в базе знаний
        target_answer = dataframe.loc[dataframe['Вопрос из БЗ'] == target_q].iloc[0]
        return target_answer['Ответ из БЗ'], \
            target_answer['Классификатор 1 уровня'], \
            target_answer['Классификатор 2 уровня']
    except IndexError:
        return NO_ANSWER, "", ""


class Answer(BaseModel):
    answer: str
    class_1: str
    class_2: str


async def get_answer(question: str) -> Answer:
    loop = asyncio.get_event_loop()
    answer_text, class_1, class_2 = await loop.run_in_executor(
        None,
        get_answer_from_rag,
        question,
        basic_rag_pipeline,
    )
    return Answer(answer=answer_text, class_1=class_1 or "", class_2=class_2 or "")
