import asyncio

import toml
from aiogram import Bot, Dispatcher
from aiogram.types import Message

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
    asyncio.create_task(connection(args, status_message.chat.id, status_message.message_id, bot))