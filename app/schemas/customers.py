from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel, validate_email


class CustomerBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    document: str = Field(min_length=3, max_length=40)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=2000)
    active: bool = True

    @field_validator("name", "document")
    @classmethod
    def strip_required(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Este campo no puede estar vacío")
        return value.strip()

    @field_validator("email")
    @classmethod
    def email_is_valid(cls, value: str | None) -> str | None:
        return validate_email(value)


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    document: str | None = Field(default=None, min_length=3, max_length=40)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    address: str | None = Field(default=None, max_length=300)
    notes: str | None = Field(default=None, max_length=2000)
    active: bool | None = None

    @field_validator("email")
    @classmethod
    def email_is_valid(cls, value: str | None) -> str | None:
        return validate_email(value)


class CustomerRead(CustomerBase, ORMModel):
    id: int
    created_at: datetime
    updated_at: datetime


class CustomerList(BaseModel):
    items: list[CustomerRead]
    total: int
    page: int
    page_size: int

