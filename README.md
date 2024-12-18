# Rutube: Интеллектуальный помощник оператора службы поддержки

[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna-bot?label=bot)](https://hub.docker.com/r/airndlab/rutube-qna-bot)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna?label=qna-service)](https://hub.docker.com/r/airndlab/rutube-qna)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna-pipeline-rag-ranker?label=pipeline-rag-ranker)](https://hub.docker.com/r/airndlab/rutube-qna-pipeline-rag-ranker)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna-pipeline-faq?label=pipeline-faq)](https://hub.docker.com/r/airndlab/rutube-qna-pipeline-faq)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna-pipeline-faq-cases?label=pipeline-faq-cases)](https://hub.docker.com/r/airndlab/rutube-qna-pipeline-faq-cases)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna-pipeline-baseline?label=pipeline-baseline)](https://hub.docker.com/r/airndlab/rutube-qna-pipeline-baseline)

![Architecture](docs/images/architecture.svg)

Состав проекта (читайте подробности внутри под-проектов):

- [bot](bot) - Telegram бот
- [qna-service](qna) - Сервис ответов на вопросы
- [Пайплайны](pipelines/README.md):
    - [pipeline-rag-ranker](pipelines/rag_ranker) - Пайплайн поиска по вопросам FAQ + Кейсам с ранжированием
    - [pipeline-faq](pipelines/faq) - Пайплайн поиска по вопросам FAQ
    - [pipeline-faq-cases](pipelines/faq_cases) - Пайплайн поиска по вопросам FAQ + Кейсам
    - [pipeline-baseline](pipelines/baseline) - Пайплайн кейсхолдеров
- [Данные](data/README.md)
- [Конфигурация](config/README.md)
- [Нагрузочное тестирование](tests/README.md)

## Разработка

![Technologies](docs/images/technologies.svg)

Установить:

- python
- poetry

## Сборка

> Настроена сборка через
> [GitHub Actions](https://github.com/airndlab/hackathon-hacks-ai-rutube-qna/actions/workflows/docker.yml).

Установить:

- docker

Перейти в нужный подпроект и запустить:

```
docker build -t <название вашего образа>:<тег вашего образа> .
```

## Конфигурация

- [bot-messages.yml](config/bot-messages.yml) - настройка текста для сообщения бота

## Запуск

Установить:

- docker compose

Создать `.env`:

```properties
BOT_TOKEN=<токен вашего telegram бота>
```

Запустить:

```shell
docker compose up -d
```
