import asyncio
import json
import os
import re

import joblib
import nltk
import pandas as pd
import pymorphy2
from haystack import Document
from haystack import Pipeline
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.rankers import TransformersSimilarityRanker
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.utils import ComponentDevice
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from pydantic import BaseModel

KNOWLEDGE_BASE_FILE_PATH = os.getenv('KNOWLEDGE_BASE_FILE_PATH')
CASES_FILE_PATH = os.getenv('CASES_FILE_PATH')

df_base = pd.read_excel(KNOWLEDGE_BASE_FILE_PATH)
df_case = pd.read_excel(CASES_FILE_PATH)

combined_column = pd.concat([
    df_base['Вопрос из БЗ'],
    df_case['Вопрос пользователя'],
    df_base['Ответ из БЗ']],
    ignore_index=True)

df_base_rest = df_base.drop(columns=['Вопрос из БЗ'])
df_case_rest = df_case.drop(columns=['Вопрос пользователя'])

combined_rest = pd.concat([df_base_rest, df_case_rest, df_base_rest], ignore_index=True)

final_df = combined_rest.copy()
final_df['Вопрос'] = combined_column

final_df = final_df[['Вопрос'] + [col for col in final_df.columns if col != 'Вопрос']]
final_df = final_df.drop(columns=["Тема"])

docs = [Document(content=row["Вопрос"], meta={"idx": index}) for index, row in final_df.iterrows()]

"""### Инициализируем Трансформер для построения эмбеддинга вопросов"""

device = ComponentDevice.from_str("cuda:0")

# embed_model = "cointegrated/LaBSE-en-ru"
embed_model = "intfloat/e5-large-v2"

doc_embedder = SentenceTransformersDocumentEmbedder(
    model=embed_model,
    device=device,
    model_kwargs={"max_length": 512, "do_truncate": True},
)

doc_embedder.warm_up()

document_store = InMemoryDocumentStore()

docs_with_embeddings = doc_embedder.run(docs)
unique_docs = {doc.id: doc for doc in docs_with_embeddings["documents"]}.values()
document_store.write_documents(list(unique_docs))

text_embedder = SentenceTransformersTextEmbedder(
    model=embed_model,
    device=device,
    model_kwargs={"max_length": 512}
)

retriever = InMemoryEmbeddingRetriever(document_store, top_k=50)

ranker = TransformersSimilarityRanker(
    model="DiTy/cross-encoder-russian-msmarco",
    top_k=1,
    model_kwargs={"max_length": 512},
    tokenizer_kwargs={"model_max_length": 512}
)

basic_rag_pipeline = Pipeline()
# Add components to your pipeline
basic_rag_pipeline.add_component("text_embedder", text_embedder)
basic_rag_pipeline.add_component("retriever", retriever)
basic_rag_pipeline.add_component("ranker", ranker)

# Now, connect the components to each other
basic_rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
basic_rag_pipeline.connect("retriever", "ranker")

"""Добавим словарь, по которому будем заменять англицизмы на действительно английские слова (т. к. в базе они хранятся именно на английском)"""

# Загрузка замен слов на их эквиваленты из файла
REPLACEMENTS_FILE_PATH = os.getenv('REPLACEMENTS_FILE_PATH')
with open(REPLACEMENTS_FILE_PATH, 'r', encoding='utf-8') as file:
    replace_dict = json.load(file)

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('russian'))

loaded_models = {}
loaded_encoders = {}
loaded_vectorizers = {}


def preprocess(text):
    text = re.sub(r'\W+', ' ', text)

    words = nltk.word_tokenize(text)
    words = [lemmatizer.lemmatize(word) for word in words if word not in stop_words]

    return ' '.join(words)


def load_model_and_files(model_name, model_path, encoder_path, vectorizer_path):
    global loaded_models, loaded_encoders, loaded_vectorizers

    if model_name not in loaded_models:
        print(f"Загрузка модели {model_name}...")
        loaded_models[model_name] = joblib.load(model_path)
        loaded_encoders[model_name] = joblib.load(encoder_path)
        loaded_vectorizers[model_name] = joblib.load(vectorizer_path)
    else:
        print(f"Модель {model_name} уже загружена.")


def classify_question(
        question_text: str,
        model_name: str,
):
    global loaded_models, loaded_encoders, loaded_vectorizers

    preprocessed_question = preprocess(question_text)

    # Преобразование вопроса в TF-IDF вектор
    vectorizer = loaded_vectorizers[model_name]
    question_tfidf = vectorizer.transform([preprocessed_question])

    # Предсказание с помощью модели
    model = loaded_models[model_name]
    predicted_label_numeric = model.predict(question_tfidf)

    # Преобразование числовой метки обратно в текстовую метку
    encoder = loaded_encoders[model_name]
    predicted_label_text = encoder.inverse_transform(predicted_label_numeric)

    return predicted_label_text[0]


model_path_1 = "model_1/classifier_1.pkl"
encoder_path_1 = "model_1/label_encoder_1.pkl"
vectorizer_path_1 = "model_1/vectorizer_1.pkl"

model_path_2 = "model_2/classifier_2.pkl"
encoder_path_2 = "model_2/label_encoder_2.pkl"
vectorizer_path_2 = "model_2/vectorizer_2.pkl"

load_model_and_files('model_1', model_path_1, encoder_path_1, vectorizer_path_1)
load_model_and_files('model_2', model_path_2, encoder_path_2, vectorizer_path_2)

"""### Интерфейс для получения ответа из RAG пайплайна"""

morph = pymorphy2.MorphAnalyzer()


def preprocess_text(text):
    """
    Функция предобработки текста: приведение к нижнему регистру, удаление лишних символов,
    лемматизация и замена слов по словарю, с сохранением знаков препинания.
    Если слово не найдено в replace_dict, оно остаётся в исходной форме.
    """
    # Токенизация: разделяем слова и знаки препинания
    tokens = re.findall(r'\w+|[^\w\s]', text.lower())
    processed_tokens = []

    for token in tokens:
        if re.match(r'\w+', token):  # Если это слово
            if replace_dict and token in replace_dict:
                # Заменяем слово, если оно есть в словаре
                processed_tokens.append(replace_dict[token])
            else:
                # Если нет в словаре замен, оставляем слово как есть
                processed_tokens.append(token)
        else:
            # Знак препинания остаётся без изменений
            processed_tokens.append(token)

    # Восстановление текста с правильным расположением знаков препинания
    processed_text = ''
    for i, token in enumerate(processed_tokens):
        if token in '.,!?;:':
            # Прикрепляем знак препинания к предыдущему слову без пробела
            processed_text = processed_text.rstrip() + token + ' '
        else:
            processed_text += token + ' '

    return processed_text.strip()


def get_answer_from_rag(
        question_text: str,
        rag_pipeline,
        threshold: float = 0.25,
        df: pd.DataFrame = final_df,
):
    question_text = preprocess_text(question_text)

    response = rag_pipeline.run({"text_embedder": {"text": question_text}, "ranker": {"query": question_text}})

    document = response['ranker']['documents'][0]

    target_q = document.content
    score = document.score

    if score < threshold:
        answer_text = "Ответ не найден."
        class_1 = classify_question(question_text, "model_1")
        class_2 = classify_question(question_text, "model_2")
    else:
        target_answer = df.loc[df['Вопрос'] == target_q].iloc[0]

        answer_text = target_answer['Ответ из БЗ']
        class_1 = target_answer['Классификатор 1 уровня']
        class_2 = target_answer['Классификатор 2 уровня']

    return answer_text, class_1, class_2


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
