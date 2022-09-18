import random
import string
from typing import Literal

from pydantic import BaseModel, Field

def _generate_hash() -> str:
    return str.join('', random.choices(string.ascii_lowercase + string.digits, k=11))

class JoinMessage(BaseModel):
    hash: str = Field(default_factory=_generate_hash)

class Params(BaseModel):
    prompt: str
    images: int = 4
    steps: int = 45
    guidance_scale: float = 7.5
    seed: int = Field(default_factory=lambda: random.randint(0, 2**31))

    def to_list(self):
        return [self.prompt, self.images, self.guidance_scale, self.seed]

class Request(BaseModel):
    fn_index = 1
    data: Params

    class Config:
        json_encoders = {
            Params: Params.to_list
        }

class Output(BaseModel):
    data: list[list[str]]
    duration: float
    average_duration: float

class Done(BaseModel):
    msg: Literal['process_completed']
    success: Literal[True]
    output: Output = None

class Fail(BaseModel):
    msg: Literal['process_completed']
    success: Literal[False]
    error: str | None

class DataRequested(BaseModel):
    msg: Literal['send_data']

class EstimationUpdate(BaseModel):
    msg: Literal['estimation']
    rank: int
    queue_size: int
    rank_eta: float

class ProcessStarts(BaseModel):
    msg: Literal['process_starts']

Message = EstimationUpdate | DataRequested | ProcessStarts | Done | Fail

class Config(BaseModel):
    token: str