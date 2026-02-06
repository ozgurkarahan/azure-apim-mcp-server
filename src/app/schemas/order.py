import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from src.app.models.order import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer_id: uuid.UUID
    shipping_address: str | None = None
    notes: str | None = None
    items: list[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    shipping_address: str | None = None
    notes: str | None = None


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    customer_id: uuid.UUID
    status: OrderStatus
    total_amount: Decimal
    currency: str
    shipping_address: str | None
    notes: str | None
    ordered_at: datetime
    shipped_at: datetime | None
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}
