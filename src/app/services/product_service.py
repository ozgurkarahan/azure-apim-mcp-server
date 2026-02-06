import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.product import Product
from src.app.schemas.product import ProductCreate, ProductUpdate


async def list_products(
    db: AsyncSession,
    category: str | None = None,
    family: str | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Product]:
    query = select(Product).where(Product.is_active.is_(True))
    if category:
        query = query.where(Product.category.ilike(f"%{category}%"))
    if family:
        query = query.where(Product.family.ilike(f"%{family}%"))
    if search:
        query = query.where(
            Product.name.ilike(f"%{search}%")
            | Product.part_number.ilike(f"%{search}%")
            | Product.description.ilike(f"%{search}%")
        )
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_product(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    return await db.get(Product, product_id)


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


async def update_product(db: AsyncSession, product_id: uuid.UUID, data: ProductUpdate) -> Product | None:
    product = await db.get(Product, product_id)
    if not product:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    await db.commit()
    await db.refresh(product)
    return product


async def soft_delete_product(db: AsyncSession, product_id: uuid.UUID) -> Product | None:
    product = await db.get(Product, product_id)
    if not product:
        return None
    product.is_active = False
    await db.commit()
    await db.refresh(product)
    return product
