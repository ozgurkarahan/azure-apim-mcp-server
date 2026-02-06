from fastapi import FastAPI

from src.app.routers import health, customers, products, orders

app = FastAPI(
    title="ST Micro Semiconductor Orders API",
    description="API for managing ST Microelectronics semiconductor orders, customers, and products.",
    version="1.0.0",
)

app.include_router(health.router)
app.include_router(customers.router)
app.include_router(products.router)
app.include_router(orders.router)
