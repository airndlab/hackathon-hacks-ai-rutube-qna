import asyncio
import json
import os
import re

import joblib
import nltk
import pandas as pd
import pymorphy2
from haystack import Document, Pipeline
from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
from haystack.components.rankers import TransformersSimilarityRanker
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.utils import ComponentDevice
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from pydantic import BaseModel

# Пути к файлам базы знаний и кейсов
KNOWLEDGE_BASE_FILE_PATH = os.getenv('KNOWLEDGE_BASE_FILE_PATH')
CASES_FILE_PATH = os.getenv('CASES_FILE_PATH')

# Чтение данных из файлов Excel
df_base = pd.read_excel(KNOWLEDGE_BASE_FILE_PATH)
df_case = pd.read_excel(CASES_FILE_PATH)

# Объединение колонок с вопросами и ответами из базы знаний и кейсов
combined_column = pd.concat([df_base['Вопрос из БЗ'], df_case['Вопрос пользователя'], df_base['Ответ из БЗ']],
                            ignore_index=True)

# Удаление колонок с вопросами для последующего объединения данных
df_base_rest = df_base.drop(columns=['Вопрос из БЗ'])
df_case_rest = df_case.drop(columns=['Вопрос пользователя'])

# Объединение оставшихся колонок
combined_rest = pd.concat([df_base_rest, df_case_rest, df_base_rest], ignore_index=True)

# Создание итогового DataFrame
final_df = combined_rest.copy()
final_df['Вопрос'] = combined_column

# Перестановка колонок и удаление ненужных данных
final_df = final_df[['Вопрос'] + [col for col in final_df.columns if col != 'Вопрос']]
final_df = final_df.drop(columns=["Тема"])

# Создание списка документов для эмбеддинга
docs = [Document(content=row["Вопрос"], meta={"idx": index}) for index, row in final_df.iterrows()]

# Инициализация модели для создания эмбеддингов документов
device = ComponentDevice.from_str("cuda:0")
embed_model = "intfloat/e5-large-v2"

# Настройка эмбеддера документов
doc_embedder = SentenceTransformersDocumentEmbedder(
    model=embed_model,
    device=device,
    model_kwargs={"max_length": 512, "do_truncate": True},
)
doc_embedder.warm_up()

# Инициализация хранилища документов в памяти
document_store = InMemoryDocumentStore()
docs_with_embeddings = doc_embedder.run(docs)

# Уникальные документы и запись их в хранилище
unique_docs = {doc.id: doc for doc in docs_with_embeddings["documents"]}.values()
document_store.write_documents(list(unique_docs))

# Настройка текстового эмбеддера для последующего поиска по эмбеддингам
text_embedder = SentenceTransformersTextEmbedder(
    model=embed_model,
    device=device,
    model_kwargs={"max_length": 512}
)

# Инициализация Retriever для поиска по эмбеддингам
retriever = InMemoryEmbeddingRetriever(document_store, top_k=50)

# Настройка ранжировщика для сопоставления вопросов и ответов
ranker = TransformersSimilarityRanker(
    model="DiTy/cross-encoder-russian-msmarco",
    top_k=1,
    model_kwargs={"max_length": 512},
    tokenizer_kwargs={"model_max_length": 512}
)

# Сборка пайплайна RAG (Retrieval-Augmented Generation)
basic_rag_pipeline = Pipeline()
basic_rag_pipeline.add_component("text_embedder", text_embedder)
basic_rag_pipeline.add_component("retriever", retriever)
basic_rag_pipeline.add_component("ranker", ranker)

# Соединение компонентов пайплайна
basic_rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
basic_rag_pipeline.connect("retriever", "ranker")

# Загрузка словаря замен из файла для корректной обработки англицизмов
REPLACEMENTS_FILE_PATH = os.getenv('REPLACEMENTS_FILE_PATH')
with open(REPLACEMENTS_FILE_PATH, 'r', encoding='utf-8') as file:
    replace_dict = json.load(file)

# Загрузка необходимых ресурсов NLTK для обработки текста
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('russian'))

# Глобальные словари для хранения загруженных моделей, энкодеров и векторизаторов
loaded_models = {}
loaded_encoders = {}
loaded_vectorizers = {}


# Функция предобработки текста
def preprocess(text):
    text = re.sub(r'\W+', ' ', text)
    words = nltk.word_tokenize(text)
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]
    return ' '.join(words)


# Загрузка модели и связанных файлов
def load_model_and_files(model_name, model_path, encoder_path, vectorizer_path):
    global loaded_models, loaded_encoders, loaded_vectorizers
    if model_name not in loaded_models:
        print(f"Загрузка модели {model_name}...")
        loaded_models[model_name] = joblib.load(model_path)
        loaded_encoders[model_name] = joblib.load(encoder_path)
        loaded_vectorizers[model_name] = joblib.load(vectorizer_path)
    else:
        print(f"Модель {model_name} уже загружена.")


# Классификация вопроса на основе загруженных моделей
def classify_question(question: str, model_name: str):
    global loaded_models, loaded_encoders, loaded_vectorizers
    preprocessed_question = preprocess(question)
    vectorizer = loaded_vectorizers[model_name]
    question_tfidf = vectorizer.transform([preprocessed_question])
    model = loaded_models[model_name]
    predicted_label_numeric = model.predict(question_tfidf)
    encoder = loaded_encoders[model_name]
    predicted_label_text = encoder.inverse_transform(predicted_label_numeric)
    return predicted_label_text[0]


# Пути к моделям, энкодерам и векторизаторам
model_path_1 = "model_1/classifier_1.pkl"
encoder_path_1 = "model_1/label_encoder_1.pkl"
vectorizer_path_1 = "model_1/vectorizer_1.pkl"

model_path_2 = "model_2/classifier_2.pkl"
encoder_path_2 = "model_2/label_encoder_2.pkl"
vectorizer_path_2 = "model_2/vectorizer_2.pkl"

# Загрузка всех моделей и файлов
load_model_and_files('model_1', model_path_1, encoder_path_1, vectorizer_path_1)
load_model_and_files('model_2', model_path_2, encoder_path_2, vectorizer_path_2)

# Инициализация морфологического анализатора
morph = pymorphy2.MorphAnalyzer()


# Функция предобработки текста с использованием словаря замен
def preprocess_text(text):
    tokens = re.findall(r'\w+|[^\w\s]', text.lower())
    processed_tokens = []
    for token in tokens:
        if re.match(r'\w+', token):
            processed_tokens.append(replace_dict.get(token, token))
        else:
            processed_tokens.append(token)
    processed_text = ' '.join(processed_tokens).strip()
    return processed_text


# Функция получения ответа из RAG пайплайна
def get_answer_from_rag(question: str, rag_pipeline, threshold: float = 0.25, df: pd.DataFrame = final_df):
    question = preprocess_text(question)
    response = rag_pipeline.run({"text_embedder": {"text": question}, "ranker": {"query": question}})
    document = response['ranker']['documents'][0]
    target_q = document.content
    score = document.score
    if score < threshold:
        answer_text = "Ответ не найден."
        class_1 = classify_question(question, "model_1")
        class_2 = classify_question(question, "model_2")
    else:
        target_answer = df.loc[df['Вопрос'] == target_q].iloc[0]
        answer_text = target_answer['Ответ из БЗ']
        class_1 = target_answer['Классификатор 1 уровня']
        class_2 = target_answer['Классификатор 2 уровня']
    return answer_text, class_1, class_2


# Асинхронная функция для получения ответа из RAG пайплайна
class Answer(BaseModel):
    answer: str
    class_1: str
    class_2: str


async def get_answer(question: str) -> Answer:
    loop = asyncio.get_event_loop()
    answer_text, class_1, class_2 = await loop.run_in_executor(None, get_answer_from_rag, question, basic_rag_pipeline)
    return Answer(answer=answer_text, class_1=class_1 or "", class_2=class_2 or "")
