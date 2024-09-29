# Сервис ответов на вопросы

## Конфигурация через env

Опциональные:

- `QNA_DB_PATH` - путь до файла с бд, значение по-умолчанию `metrics.db`
- `QNA_SERVICE_DEFAULT_PIPELINE` - по-умолчанию пайплайн,
  значение по-умолчанию `rag_ranker`
- `PIPELINE_BASELINE_SERVICE_URL` - адрес `pipeline-baseline`,
  значение по-умолчанию `http://pipeline-baseline:8088`
- `PIPELINE_FAQ_SERVICE_URL` - адрес `pipeline-faq`,
  значение по-умолчанию `http://pipeline-faq:8088`
- `PIPELINE_FAQ_CASES_SERVICE_URL` - адрес `pipeline-faq-cases`,
  значение по-умолчанию `http://pipeline-faq-cases:8088`
- `PIPELINE_RAG_RANKER_SERVICE_URL` - адрес `pipeline-rag-ranker`,
  значение по-умолчанию `http://pipeline-rag-ranker:8088`
