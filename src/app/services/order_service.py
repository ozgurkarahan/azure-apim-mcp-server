import uuid
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.app.models.order import Order, OrderStatus
from src.app.models.order_item import OrderItem
from src.app.models.product import Product
from src.app.schemas.order import OrderCreate, OrderUpdate


async def _generate_order_number(db: AsyncSession) -> str:
    now = datetime.now(timezone.utc)
    prefix = f"ST-ORD-{now.strftime('%Y%m')}-"
    result = await db.execute(
        select(func.count()).where(Order.order_number.like(f"{prefix}%"))
    )
    count = result.scalar_one() + 1
    return f"{prefix}{count:04d}"


async def list_orders(
    db: AsyncSession,
    status: OrderStatus | None = None,
    customer_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Order]:
    query = select(Order).options(selectinload(Order.items))
    if status:
        query = query.where(Order.status == status)
    if customer_id:
        query = query.where(Order.customer_id == customer_id)
    query = query.order_by(Order.ordered_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_order(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    query = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_order(db: AsyncSession, data: OrderCreate) -> Order:
    order_number = await _generate_order_number(db)
    order = Order(
        order_number=order_number,
        customer_id=data.customer_id,
        shipping_address=data.shipping_address,
        notes=data.notes,
        status=OrderStatus.pending,
    )

    total = 0
    for item_data in data.items:
        product = await db.get(Product, item_data.product_id)
        if not product:
            raise ValueError(f"Product {item_data.product_id} not found")
        line_total = product.unit_price * item_data.quantity
        item = OrderItem(
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=product.unit_price,
            line_total=line_total,
        )
        order.items.append(item)
        total += line_total

    order.total_amount = total
    db.add(order)
    await db.commit()
    await db.refresh(order)
    # Reload with items
    return await get_order(db, order.id)


async def update_order(db: AsyncSession, order_id: uuid.UUID, data: OrderUpdate) -> Order | None:
    order = await get_order(db, order_id)
    if not order:
        return None

    update_data = data.model_dump(exclude_unset=True)
    now = datetime.now(timezone.utc)

    if "status" in update_data:
        new_status = update_data["status"]
        if new_status == OrderStatus.shipped and not order.shipped_at:
            order.shipped_at = now
        elif new_status == OrderStatus.delivered and not order.delivered_at:
            order.delivered_at = now

    for key, value in update_data.items():
        setattr(order, key, value)

    await db.commit()
    return await get_order(db, order_id)


async def cancel_order(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    order = await get_order(db, order_id)
    if not order:
        return None
    order.status = OrderStatus.cancelled
    await db.commit()
    return await get_order(db, order_id)
