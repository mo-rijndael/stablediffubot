import asyncio

import toml
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from pydantic.errors import PydanticValueError, PydanticTypeError

from connection import connection
from models import Params

config = toml.load(open("./config.toml"))
bot = Bot(config['token'])
dispatcher = Dispatcher(bot)

@dispatcher.message_handler(run_task=True)
async def process_request(message: Message):
    if not message.text:
        await message.answer("Нейросеть понимает только запросы текстом")
        return
    status_message = await message.answer("Принято! Прогресс буду обновлять в реальном времени редактируя это сообщение")
    args = Params(prompt=message.text)
    try:
        await connection(args, status_message)
    except (PydanticValueError, PydanticTypeError):
        await status_message.edit_text("Сервер прислал какую-то совершенно неадекватную херню")
