import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.customer import Customer
from src.app.schemas.customer import CustomerCreate, CustomerUpdate


async def list_customers(
    db: AsyncSession,
    search: str | None = None,
    country: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Customer]:
    query = select(Customer)
    if search:
        query = query.where(
            Customer.company_name.ilike(f"%{search}%") | Customer.contact_name.ilike(f"%{search}%")
        )
    if country:
        query = query.where(Customer.country.ilike(f"%{country}%"))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_customer(db: AsyncSession, customer_id: uuid.UUID) -> Customer | None:
    return await db.get(Customer, customer_id)


async def create_customer(db: AsyncSession, data: CustomerCreate) -> Customer:
    customer = Customer(**data.model_dump())
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


async def update_customer(db: AsyncSession, customer_id: uuid.UUID, data: CustomerUpdate) -> Customer | None:
    customer = await db.get(Customer, customer_id)
    if not customer:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, key, value)
    await db.commit()
    await db.refresh(customer)
    return customer
