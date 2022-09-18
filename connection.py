import base64
from io import BytesIO

import aiohttp
import pydantic
import websockets
from aiogram import Bot
from aiogram.types import MediaGroup, InputFile

from models import Params, Message, JoinMessage, EstimationUpdate, DataRequested, Done, ProcessStarts, Request, Output, \
    Fail


def _extract_pics(data: Output) -> list[BytesIO]:
    return [BytesIO(base64.b64decode(pic)) for pic in data.data[0]]

async def connection(params: Params, chat_id: int, message_id: int, bot: Bot):
    session = JoinMessage()
    async with aiohttp.ClientSession() as client:
        get_seed_params = {"data": [], "fn_index": 4, "session_hash": session.hash}
        async with client.post("https://hf.space/embed/stabilityai/stable-diffusion/api/predict/", json=get_seed_params) as request:
            response = await request.json()
    print(response)
    [seed] = response['data']
    params.seed = seed

    async with websockets.connect("wss://spaces.huggingface.tech/stabilityai/stable-diffusion/queue/join") as ws:
        await ws.send(session.json())
        async for m in ws:
            if len(m) < 1000:
                print(m)
            message = pydantic.parse_raw_as(Message, m)
            match message:
                case EstimationUpdate(rank=rank, queue_size=size, rank_eta=eta):
                    await bot.edit_message_text(f"В очереди: {rank + 1} из {size}. Осталось примерно: {eta:.2f} сек", chat_id, message_id)
                case DataRequested():
                    data = Request(data=params).json(models_as_dict=False)
                    print(data)
                    await ws.send(data)
                case ProcessStarts():
                    await bot.edit_message_text("В обработке. Уже скоро!", chat_id, message_id)
                case Done(output=output):
                    media = MediaGroup()
                    caption = (f"Сгенерировано Stable Diffusion по запросу "
                               f"«{params.prompt}»\n"
                               f"seed: {params.seed}")
                    for photo in _extract_pics(output):
                        media.attach_photo(InputFile(photo), caption=caption)
                    await bot.delete_message(chat_id, message_id)
                    await bot.send_media_group(chat_id, media)
                case Fail(error=error):
                    await bot.edit_message_text(f"Сервер вернул ошибку «{error}» вместо результатов. Ничо не могу сделать", chat_id, message_id)