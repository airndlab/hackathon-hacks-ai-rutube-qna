import asyncio
import logging
import os

import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from settings import init_db, set_pipeline, get_pipeline_or_default
from qna import get_answer, Answer, pipelines, default_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    text = (
        f'Здравствуйте, {message.from_user.full_name}!\n'
        f'Я интеллектуальный помощник Rutube.\n'
        f'Готов ответить на Ваши вопросы.'
    )
    await message.reply(text)


async def get_pipelines_text():
    pipelines_list = "\n\n".join([f"- /pipeline {name}: {description}" for name, description in pipelines.items()])
    response = f"Доступные пайплайны:\n\n{pipelines_list}"
    return response


@dp.message(Command('pipelines'))
async def command_pipelines_handler(message: Message):
    current_pipeline = await get_pipeline_or_default(message.chat.id)
    pipelines_text = await get_pipelines_text()
    text = f'Текущий пайплайн: {current_pipeline}\n\n{pipelines_text}'
    await message.reply(text)


@dp.message(Command('pipeline'))
async def command_pipelines_handler(message: Message):
    args = message.text.split()
    if len(args) != 2:
        text = f"Пожалуйста, укажите название пайплайна.\n\nПример: /pipeline {default_pipeline}"
        await message.reply(text)
        return
    pipeline_name = args[1]
    if pipeline_name in pipelines:
        await set_pipeline(message.chat.id, pipeline_name)
        response = f"Выбран пайплайн {pipeline_name}: {pipelines[pipeline_name]}"
    else:
        response = f'Пайплайн не найден. {get_pipelines_text()}'
    await message.answer(response)


def get_answer_text(response: Answer) -> str:
    return f'{response.answer}\n\nКлассификатор 1: {response.class_1}\nКлассификатор 2: {response.class_2}'


@dp.message()
async def question_handler(message: Message) -> None:
    try:
        question = message.text
        pipeline = await get_pipeline_or_default(message.chat.id)
        answer = await get_answer(question, pipeline)
        text = get_answer_text(answer)
        await message.reply(text)
    except Exception as e:
        await message.reply(f'Ой! Произошла непредвиденная ошибка, нам очень жаль...\n\n{e}')
        raise e


async def main() -> None:
    bot_token = os.getenv('BOT_TOKEN')
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
