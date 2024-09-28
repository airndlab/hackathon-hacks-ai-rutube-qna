import asyncio
import json
import os
import re
import warnings

import pandas as pd
import pymorphy2
from haystack import Document, Pipeline
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.utils import ComponentDevice
from pydantic import BaseModel

NO_ANSWER = "Ответ не найден."

warnings.filterwarnings('ignore')

# Путь к файлам базы знаний и кейсов из переменных окружения
KNOWLEDGE_BASE_FILE_PATH = os.getenv('KNOWLEDGE_BASE_FILE_PATH')
CASES_FILE_PATH = os.getenv('CASES_FILE_PATH')

# Загрузка данных из файлов
df_base = pd.read_excel(KNOWLEDGE_BASE_FILE_PATH)
df_case = pd.read_excel(CASES_FILE_PATH)

# Объединение вопросов из БЗ и пользовательских вопросов в один столбец
combined_column = pd.concat([df_base['Вопрос из БЗ'], df_case['Вопрос пользователя']], ignore_index=True)

# Объединение остальных данных и создание итогового DataFrame
df_base_rest = df_base.drop(columns=['Вопрос из БЗ'])
df_case_rest = df_case.drop(columns=['Вопрос пользователя'])
combined_rest = pd.concat([df_base_rest, df_case_rest], ignore_index=True)
final_df = combined_rest.copy()
final_df['Вопрос'] = combined_column
final_df = final_df[['Вопрос'] + [col for col in final_df.columns if col != 'Вопрос']]
final_df = final_df.drop(columns=["Тема"])

# Создание документов для RAG pipeline
docs = [Document(content=row["Вопрос"], meta={"idx": index}) for index, row in final_df.iterrows()]

# Настройка устройства и моделей эмбеддинга
device = ComponentDevice.from_str("cuda:0")
embed_model = "intfloat/e5-large-v2"
doc_embedder = SentenceTransformersDocumentEmbedder(model=embed_model, device=device)
doc_embedder.warm_up()
document_store = InMemoryDocumentStore()
docs_with_embeddings = doc_embedder.run(docs)
unique_docs = {doc.id: doc for doc in docs_with_embeddings["documents"]}.values()
document_store.write_documents(list(unique_docs))

# Настройка RAG pipeline
text_embedder = SentenceTransformersTextEmbedder(model=embed_model, device=device)
retriever = InMemoryEmbeddingRetriever(document_store, top_k=1)
basic_rag_pipeline = Pipeline()
basic_rag_pipeline.add_component("text_embedder", text_embedder)
basic_rag_pipeline.add_component("retriever", retriever)
basic_rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")

# Загрузка замен слов на их эквиваленты из файла
REPLACEMENTS_FILE_PATH = os.getenv('REPLACEMENTS_FILE_PATH')
with open(REPLACEMENTS_FILE_PATH, 'r', encoding='utf-8') as file:
    replace_dict = json.load(file)


def get_answer_from_rag(question: str, rag_pipeline, df: pd.DataFrame = final_df):
    """
    Обрабатывает вопрос, заменяет слова по словарю, запускает поиск через RAG pipeline и возвращает ответ.
    """
    morph = pymorphy2.MorphAnalyzer()

    # Приведение вопроса к нижнему регистру и удаление знаков препинания
    question = question.lower()
    question = re.sub(r'[^\w\s-]', '', question)

    # Замена слов на основе словаря
    if replace_dict:
        words = question.split()
        replaced_words = [replace_dict.get(morph.parse(word)[0].normal_form, word) for word in words]
        question = ' '.join(replaced_words)

    print(f"Processed question: {question}")

    # Запуск RAG pipeline для поиска ответа
    response = rag_pipeline.run({"text_embedder": {"text": question}})

    # Извлечение ответа из полученных документов
    try:
        target_q = response['retriever']['documents'][0].content
    except (IndexError, KeyError):
        return "Документы не найдены в ответе RAG pipeline.", "", ""

    try:
        target_answer = df.loc[df['Вопрос'] == target_q].iloc[0]
        return target_answer['Ответ из БЗ'], target_answer['Классификатор 1 уровня'], target_answer[
            'Классификатор 2 уровня']
    except IndexError:
        return NO_ANSWER, "", ""


class Answer(BaseModel):
    answer: str
    class_1: str
    class_2: str


async def get_answer(question: str) -> Answer:
    """
    Асинхронная функция для получения ответа на вопрос с использованием RAG pipeline.
    """
    loop = asyncio.get_event_loop()
    answer_text, class_1, class_2 = await loop.run_in_executor(None, get_answer_from_rag, question, basic_rag_pipeline)
    return Answer(answer=answer_text, class_1=class_1 or "", class_2=class_2 or "")
