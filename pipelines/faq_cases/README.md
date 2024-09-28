# Пайплайн поиска по вопросам FAQ+Кейсы

RAG и модель `intfloat/e5-large-v2`,
подробнее смотрите в тетрадке [rag_faq_cases.ipynb](rag_faq_cases.ipynb).

## Конфигурация через env

Обязательные к заполнению:

- `KNOWLEDGE_BASE_FILE_PATH` - путь к файлу с базой знаний
- `CASES_FILE_PATH` - путь к файлу с реальными кейсами
- `REPLACEMENTS_FILE_PATH` - путь к файлу с заменами слов на их эквиваленты
