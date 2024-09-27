import asyncio
import logging
import os

import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message

from qna import get_answer, Answer

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
    await message.answer(text)


def get_answer_text(response: Answer) -> str:
    return f'{response.answer}\n\nКлассификатор 1: {response.class_1}\nКлассификатор 2: {response.class_2}'


@dp.message()
async def question_handler(message: Message) -> None:
    try:
        question = message.text
        answer = await get_answer(question)
        text = get_answer_text(answer)
        await message.reply(text)
    except Exception as e:
        await message.answer(f'Ой! Произошла непредвиденная ошибка, нам очень жаль...\n\n{e}')
        raise e


async def main() -> None:
    bot_token = os.getenv('BOT_TOKEN')
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
