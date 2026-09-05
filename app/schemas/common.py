from __future__ import annotations

import re
from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict


Money = Annotated[Decimal, AfterValidator(lambda value: value.quantize(Decimal("0.01")))]


def validate_email(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    value = value.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise ValueError("El correo electrónico no tiene un formato válido")
    return value


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    message: str

