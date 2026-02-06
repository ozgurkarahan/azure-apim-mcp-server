import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ProductCreate(BaseModel):
    part_number: str
    name: str
    description: str | None = None
    category: str
    family: str | None = None
    unit_price: Decimal
    currency: str = "USD"
    stock_quantity: int = 0
    lead_time_days: int | None = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    family: str | None = None
    unit_price: Decimal | None = None
    currency: str | None = None
    stock_quantity: int | None = None
    lead_time_days: int | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    part_number: str
    name: str
    description: str | None
    category: str
    family: str | None
    unit_price: Decimal
    currency: str
    stock_quantity: int
    lead_time_days: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
