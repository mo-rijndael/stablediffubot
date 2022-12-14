import toml
from aiogram import Bot, Dispatcher
from aiogram.types import Message

from connection import connection, QueueLooksTooBig
from models import Params

config = toml.load(open("./config.toml"))
bot = Bot(config['token'])
dispatcher = Dispatcher(bot)

@dispatcher.message_handler(commands=['start'])
async def start(message: Message):
    await message.answer("Привет! Чтобы начать генерировать, просто напиши затравку для нейросети")

@dispatcher.message_handler(commands=['help'])
async def help_(message: Message):
    await message.answer("Для генерации используется неофициально апи "
                         "[этой](https://huggingface.co/spaces/stabilityai/stable-diffusion) демки"
                         "\n\n"
                         "Параметры по умолчанию:\n"
                         "картинки: 4\n"
                         "шаги: 45\n"
                         "Guidance scale: 7.5\n"
                         "seed: случайный\n"
                         "изменение параметров: пока не реализовано :(",
                         parse_mode='MARKDOWN')


@dispatcher.message_handler(run_task=True)
async def process_request(message: Message):
    if not message.text:
        await message.answer("Нейросеть понимает только запросы текстом")
        return
    status_message = await message.answer("Принято!")
    args = Params(prompt=message.text)
    try:
        await connection(args, status_message)
    except QueueLooksTooBig:
        await connection(args, status_message, try_better_place=False)
