import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from src.app.services import customer_service

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


@router.get("", response_model=list[CustomerResponse])
async def list_customers(
    search: str | None = Query(None),
    country: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await customer_service.list_customers(db, search=search, country=country, skip=skip, limit=limit)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    customer = await customer_service.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=CustomerResponse, status_code=201)
async def create_customer(data: CustomerCreate, db: AsyncSession = Depends(get_db)):
    return await customer_service.create_customer(db, data)


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: uuid.UUID, data: CustomerUpdate, db: AsyncSession = Depends(get_db)):
    customer = await customer_service.update_customer(db, customer_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer
