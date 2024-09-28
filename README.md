# Rutube: Интеллектуальный помощник оператора службы поддержки

[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna-bot?label=rutube-qna-bot)](https://hub.docker.com/r/airndlab/rutube-qna-bot)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna?label=rutube-qna)](https://hub.docker.com/r/airndlab/rutube-qna)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna-pipeline-faq?label=rutube-qna-pipeline-faq)](https://hub.docker.com/r/airndlab/rutube-qna-pipeline-faq)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna-pipeline-faq-cases?label=rutube-qna-pipeline-faq-cases)](https://hub.docker.com/r/airndlab/rutube-qna-pipeline-faq-cases)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/airndlab/rutube-qna-pipeline-baseline?label=rutube-qna-pipeline-baseline)](https://hub.docker.com/r/airndlab/rutube-qna-pipeline-baseline)

Rutube Q&A.

## Разработка

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

## Запуск

Установить:

- docker compose

Создать `.env`:

```properties
BOT_TOKEN=<токен вашего телеграм бота>
```

Запустить:

```shell
docker compose up -d
```
