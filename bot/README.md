# Telegram бот

Бот для ответов на вопросы.

## Конфигурация через env

Обязательные к заполнению:

- `BOT_TOKEN` - токен Telegram бота
- `BOT_MESSAGES_FILE_PATH` - путь к файлу с текстами для сообщений бота

Опциональные:

- `QNA_SERVICE_URL` - адрес `qna-service`, значение по-умолчанию `http://qna-service:8080`
- `BOT_DB_PATH` - путь до файла с бд, значение по-умолчанию `settings.db`
- `BOT_DEFAULT_VERBOSE` - по-умолчанию подробный режим, значение по-умолчанию `false`
- `BOT_DEFAULT_PIPELINE` - по-умолчанию пайплайн, значение по-умолчанию `rag_ranker`
