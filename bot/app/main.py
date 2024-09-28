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
from settings import init_db, get_pipeline_or_default, get_verbose_or_default, pipelines, set_verbose, set_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

BOT_MESSAGES_FILE_PATH = os.getenv('BOT_MESSAGES_FILE_PATH')
with open(BOT_MESSAGES_FILE_PATH, 'r', encoding='utf-8') as file:
    bot_messages = yaml.safe_load(file)

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.reply(bot_messages['start'])


@dp.message(Command('pipelines'))
async def command_pipelines_handler(message: Message):
    current_pipeline = await get_pipeline_or_default(message.chat.id)
    text = bot_messages['pipelines'].format(pipeline=pipelines[current_pipeline])
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f'pipeline:{key}')]
        for key, name in pipelines.items()
    ])
    await message.reply(text, reply_markup=markup)


@dp.callback_query(lambda query: query.data.startswith('pipeline:'))
async def pipeline_handler(query: CallbackQuery):
    pipeline_name = query.data.split(':')[1]
    await set_pipeline(query.message.chat.id, pipeline_name)
    await query.answer(bot_messages['pipeline'].format(pipeline=pipelines[pipeline_name]))


@dp.message(Command('verbose'))
async def command_verbose_handler(message: Message):
    verbose = await get_verbose_or_default(message.chat.id)
    text = bot_messages['verbose'].format(status=get_verbose_status(verbose))
    markup = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅", callback_data=f'verbose:true'),
        InlineKeyboardButton(text="❌", callback_data=f'verbose:false'),
    ]])
    await message.reply(text, reply_markup=markup)


def get_verbose_status(verbose):
    verbose_status = bot_messages['verbose-enabled'] if verbose else bot_messages['verbose-disabled']
    return verbose_status


@dp.callback_query(lambda query: query.data.startswith('verbose:'))
async def pipeline_handler(query: CallbackQuery):
    verbose_value = query.data.split(':')[1]
    verbose = verbose_value.lower() == 'true'
    await set_verbose(query.message.chat.id, verbose)
    verbose_status = get_verbose_status(verbose)
    await query.answer(bot_messages['verbose-select'].format(status=verbose_status))


def get_answer_text(response: Answer, verbose: bool) -> str:
    assurance_text = bot_messages['answer-confident'] if True else bot_messages['answer-doubtful']
    other_text = ''
    if verbose:
        other_inline = response.get_other_inline()
        if other_inline:
            other_text = other_inline
    text = bot_messages['answer'].format(
        answer=response.answer,
        class_1=response.class_1,
        class_2=response.class_2,
        assurance=assurance_text,
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
        verbose = await get_verbose_or_default(message.chat.id)
        exception = ''
        if verbose:
            exception = str(e)
        error_text = bot_messages['error'].format(exception=exception)
        await message.reply(error_text)
        raise e


@dp.callback_query(lambda query: query.data.startswith('like:'))
async def like_handler(query: CallbackQuery):
    await like_answer(query.data.split(':')[1])
    await query.answer(bot_messages['like'])


@dp.callback_query(lambda query: query.data.startswith('dislike:'))
async def like_handler(query: CallbackQuery):
    await dislike_answer(query.data.split(':')[1])
    await query.answer(bot_messages['dislike'])


async def main() -> None:
    bot_token = os.getenv('BOT_TOKEN')
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
