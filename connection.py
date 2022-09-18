import base64
from io import BytesIO

import pydantic
import websockets
from aiogram.types import MediaGroup, InputFile, Message as TelegramMessage
from loguru import logger

from models import Params, Message, JoinMessage, EstimationUpdate, DataRequested, Done, ProcessStarts, Request, Output, \
    Fail, QueueFull

_3MB = 3 * 2 ** 20
_QUEUE_URL = "wss://spaces.huggingface.tech/stabilityai/stable-diffusion/queue/join"

def _extract_pics(data: Output) -> list[BytesIO]:
    return [BytesIO(base64.b64decode(_from_data_uri(pic)))
            for pic in data.data[0]]

def _from_data_uri(uri: str) -> str:
    header = "data:image/png;base64,"
    return uri.removeprefix(header)

async def connection(params: Params, status_message: TelegramMessage):
    session = JoinMessage().json()
    async with websockets.connect(_QUEUE_URL, max_size=_3MB) as ws:
        logger.debug(session)
        await ws.send(session)
        async for m in ws:
            logger.debug(m[:500])
            message = pydantic.parse_raw_as(Message, m)
            match message:
                case QueueFull():
                    await status_message.edit_text("Очередь переполнена! Попробуйте ещё раз!")
                case EstimationUpdate(rank=rank, queue_size=size, rank_eta=eta):
                    await status_message.edit_text(f"В очереди: {rank + 1} из {size}. Осталось примерно: {eta:.2f} сек")
                case DataRequested():
                    data = Request(data=params).json(models_as_dict=False)
                    logger.debug(data)
                    await ws.send(data)
                case ProcessStarts():
                    await status_message.edit_text("В обработке. Уже скоро!")
                case Done(output=output):
                    media = MediaGroup()
                    caption = (f"Сгенерировано Stable Diffusion по запросу "
                               f"«{params.prompt}»\n"
                               f"seed: {params.seed}")
                    for photo in _extract_pics(output):
                        media.attach_photo(InputFile(photo), caption=caption)
                    await status_message.delete()
                    await status_message.answer_media_group(media)
                    return
                case Fail(error=error):
                    await status_message.edit_text(f"Сервер вернул ошибку «{error}» вместо результатов. Ничо не могу сделать")
    await status_message.edit_text("Произошла какая-то непонятная хрень и никто не знает почему")