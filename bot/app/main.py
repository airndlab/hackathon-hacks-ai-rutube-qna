#  Copyright 2024 AI RnD Lab
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

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
from settings import (init_db, get_pipeline_or_default, get_verbose_or_default,
                      pipelines, set_verbose, set_pipeline)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

NO_ANSWER = "Ответ не найден."

SCORE_THRESHOLD = float(os.getenv('SCORE_THRESHOLD', '0.75'))

# Загрузка сообщений бота из файла
BOT_MESSAGES_FILE_PATH = os.getenv('BOT_MESSAGES_FILE_PATH')
with open(BOT_MESSAGES_FILE_PATH, 'r', encoding='utf-8') as file:
    bot_messages = yaml.safe_load(file)

# Инициализация диспетчера
dp = Dispatcher()


# Команда /start для приветствия
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.reply(bot_messages['start'])


# Команда /pipelines для выбора пайплайна
@dp.message(Command('pipelines'))
async def command_pipelines_handler(message: Message):
    current_pipeline = await get_pipeline_or_default(message.chat.id)
    text = bot_messages['pipelines'].format(pipeline=pipelines[current_pipeline])
    markup = create_pipeline_markup()
    await message.reply(text, reply_markup=markup)


# Команда /verbose для включения/выключения подробного режима
@dp.message(Command('verbose'))
async def command_verbose_handler(message: Message):
    verbose = await get_verbose_or_default(message.chat.id)
    text = bot_messages['verbose'].format(status=get_verbose_status(verbose))
    markup = create_verbose_markup()
    await message.reply(text, reply_markup=markup)


# Обработчик выбранного пайплайна
@dp.callback_query(lambda query: query.data.startswith('pipeline:'))
async def pipeline_handler(query: CallbackQuery):
    pipeline_name = query.data.split(':')[1]
    await set_pipeline(query.message.chat.id, pipeline_name)
    await query.answer(bot_messages['pipeline'].format(pipeline=pipelines[pipeline_name]))


# Обработчик выбранного включения/выключения подробного режима
@dp.callback_query(lambda query: query.data.startswith('verbose:'))
async def verbose_handler(query: CallbackQuery):
    verbose_value = query.data.split(':')[1].lower() == 'true'
    await set_verbose(query.message.chat.id, verbose_value)
    verbose_status = get_verbose_status(verbose_value)
    await query.answer(bot_messages['verbose-select'].format(status=verbose_status))


# Обработчик лайка
@dp.callback_query(lambda query: query.data.startswith('like:'))
async def like_handler(query: CallbackQuery):
    await like_answer(query.data.split(':')[1])
    await query.answer(bot_messages['like'])


# Обработчик дизлайка
@dp.callback_query(lambda query: query.data.startswith('dislike:'))
async def dislike_handler(query: CallbackQuery):
    await dislike_answer(query.data.split(':')[1])
    await query.answer(bot_messages['dislike'])


# Обработчик вопросов
@dp.message()
async def question_handler(message: Message) -> None:
    try:
        question = message.text
        pipeline = await get_pipeline_or_default(message.chat.id)
        answer_data = await get_answer(question, pipeline)
        logger.info(
            f'question={question} answer="{answer_data.answer}" '
            f'user_id="{message.from_user.id}" user_id="{message.from_user.username}" '
            f'first_name="{message.from_user.first_name}" last_name="{message.from_user.last_name}"'
        )
        if answer_data.answer == NO_ANSWER:
            await message.reply(bot_messages['answer-no'])
            return
        verbose = await get_verbose_or_default(message.chat.id)
        text = get_answer_text(answer_data, verbose)
        markup = create_answer_markup(answer_data.id)
        await message.reply(text, reply_markup=markup)
    except Exception as exception:
        verbose = await get_verbose_or_default(message.chat.id)
        error_text = bot_messages['error'].format(exception=str(exception) if verbose else '')
        await message.reply(error_text)


# Создание кнопок для сообщения

def create_pipeline_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f'pipeline:{key}')]
        for key, name in pipelines.items()
    ])


def create_verbose_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅", callback_data='verbose:true'),
        InlineKeyboardButton(text="❌", callback_data='verbose:false'),
    ]])


def create_answer_markup(answer_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👍", callback_data=f'like:{answer_id}'),
        InlineKeyboardButton(text="👎", callback_data=f'dislike:{answer_id}')
    ]])


# Вспомогательные методы

def get_verbose_status(verbose: bool) -> str:
    return bot_messages['verbose-enabled'] if verbose else bot_messages['verbose-disabled']


def get_answer_text(response: Answer, verbose: bool) -> str:
    confidence = response.score >= SCORE_THRESHOLD
    assurance_text = bot_messages['answer-confident'] if confidence else bot_messages['answer-doubtful']
    docs_text = get_docs_text(response.source)
    other_text = response.get_other_inline() if verbose else ''
    return bot_messages['answer'].format(
        answer=response.answer,
        class_1=response.class_1,
        class_2=response.class_2,
        assurance=assurance_text,
        docs=docs_text,
        other=other_text
    )


def get_docs_text(source):
    unique_types = set()
    agreement_texts = []
    for item in source:
        if item['type'] == 'Agreement':
            agreement_texts.append(f"{item['type']} {item['text']}")
        else:
            unique_types.add(item['type'])
    result = '\n'.join(unique_types)
    if agreement_texts:
        result = '\n'.join(agreement_texts) + '\n' + result
    return result


async def main() -> None:
    bot_token = os.getenv('BOT_TOKEN')
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
