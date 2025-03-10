from pydantic import BaseModel, field_validator
from typing import Dict, Any
import json


class InvalidToken(Exception):
    pass


class MainHandler(BaseModel):
    client_secret: str
    method: str
    params: Dict[str, Dict[str, Dict[str, str | Dict] | str | int] | int | str]


class Params(BaseModel):
    form_id: str
    user_id: str
    points: str
    max_points: str
    form_name: str
    answer_id: str
    answers: Dict[str, Any]
    result: str

    @field_validator('answers', mode='before')
    def parse_answers(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)  # Преобразуем JSON-строку в словарь
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON string in 'answers'")
        return value

    @field_validator('result', mode='before')
    def parse_result(cls, value):
        if value == 'Тест пройден':
            return '4197'
        elif value == 'Тест провален':
            return '4199'
        return '0'


class FormRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Params
    id: int
