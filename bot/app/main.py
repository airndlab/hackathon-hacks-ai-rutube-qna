import asyncio
import logging
import os

import sys
import yaml
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from qna import get_answer, Answer, like_answer, dislike_answer
from settings import init_db, set_pipeline, get_pipeline_or_default, get_verbose_or_default, pipelines, set_verbose

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

BOT_MESSAGES_FILE_PATH = os.getenv('BOT_MESSAGES_FILE_PATH')
with open(BOT_MESSAGES_FILE_PATH, 'r', encoding='utf-8') as file:
    messages = yaml.safe_load(file)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.reply(messages['start'])


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
async def command_pipeline_handler(message: Message):
    args = message.text.split()
    if len(args) != 2:
        text = f"Пожалуйста, укажите название пайплайна."
        await message.reply(text)
        return
    pipeline_name = args[1]
    if pipeline_name in pipelines:
        await set_pipeline(message.chat.id, pipeline_name)
        response = f"Выбран пайплайн {pipeline_name}: {pipelines[pipeline_name]}"
    else:
        response = f'Пайплайн не найден. {get_pipelines_text()}'
    await message.answer(response)


@dp.message(Command('enable_verbose'))
async def command_enable_verbose_handler(message: Message):
    await set_verbose(message.chat.id, True)
    await message.answer('Подробный режим: Включен')


@dp.message(Command('disable_verbose'))
async def command_disable_verbose_handler(message: Message):
    await set_verbose(message.chat.id, False)
    await message.answer('Подробный режим: Выключен')


def get_answer_text(response: Answer, verbose: bool) -> str:
    other_text = ''
    if verbose:
        other_inline = response.get_other_inline()
        if other_inline:
            other_text = other_inline
    text = messages['answer'].format(
        answer=response.answer,
        class_1=response.class_1,
        class_2=response.class_2,
        other=other_text
    )
    return text


@dp.message()
async def question_handler(message: Message) -> None:
    try:
        question = message.text
        pipeline = await get_pipeline_or_default(message.chat.id)
        answer = await get_answer(question, pipeline)
        verbose = await get_verbose_or_default(message.chat.id)
        text = get_answer_text(answer, verbose)
        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="👍", callback_data=f'like:{answer.id}'),
            InlineKeyboardButton(text="👎", callback_data=f'dislike:{answer.id}')
        ]])
        await message.reply(text, reply_markup=markup)
    except Exception as e:
        await message.reply(f'Ой! Произошла непредвиденная ошибка, нам очень жаль...\n\n{e}')
        raise e


@dp.callback_query(lambda query: query.data.startswith('like'))
async def like_handler(query: CallbackQuery):
    await like_answer(query.data.split(':')[1])
    await query.answer(messages['like'])


@dp.callback_query(lambda query: query.data.startswith('dislike'))
async def like_handler(query: CallbackQuery):
    await dislike_answer(query.data.split(':')[1])
    await query.answer(messages['dislike'])


async def main() -> None:
    bot_token = os.getenv('BOT_TOKEN')
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
