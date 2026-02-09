import uuid
from datetime import datetime

from pydantic import BaseModel


class CustomerCreate(BaseModel):
    company_name: str
    contact_name: str
    contact_email: str
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None


class CustomerUpdate(BaseModel):
    company_name: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None


class CustomerResponse(BaseModel):
    id: uuid.UUID
    company_name: str
    contact_name: str
    contact_email: str
    phone: str | None
    address: str | None
    city: str | None
    country: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
