import base64
from io import BytesIO

import pydantic
import websockets
from aiogram.types import MediaGroup, InputFile, Message as TelegramMessage
from loguru import logger
from tenacity import retry, retry_if_exception_type as if_exception_type, \
    wait_fixed, stop_after_attempt as after_attempt

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

class QueueFullError(Exception):
    pass

class QueueLooksTooBig(Exception):
    pass

@retry(retry=if_exception_type(QueueLooksTooBig), wait=wait_fixed(0.3), stop=after_attempt(3), reraise=True)
@retry(retry=if_exception_type(QueueFullError), wait=wait_fixed(0.3))
async def connection(params: Params, status_message: TelegramMessage, try_better_place=True):
    async with websockets.connect(_QUEUE_URL, max_size=_3MB) as ws:
        session = JoinMessage().json()
        logger.debug(session)
        await ws.send(session)
        async for m in ws:
            logger.debug(m[:500])
            message = pydantic.parse_raw_as(Message, m)
            match message:
                case QueueFull():
                    raise QueueFullError()
                case EstimationUpdate(rank=rank, queue_size=size, rank_eta=eta):
                    if try_better_place and rank > 10:
                        raise QueueLooksTooBig()
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
                    await status_message.edit_text("Высылаю результат...")
                    await status_message.answer_media_group(media)
                    await status_message.delete()
                    return
                case Fail(error=error):
                    await status_message.edit_text(f"Сервер вернул ошибку «{error}» вместо результатов. Ничо не могу сделать")
                    return
    await status_message.edit_text("Произошла какая-то непонятная хрень и никто не знает почему")