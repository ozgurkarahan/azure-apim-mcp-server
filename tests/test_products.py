import pytest


PRODUCT_DATA = {
    "part_number": "STM32F407VGT6",
    "name": "STM32F407 MCU",
    "description": "ARM Cortex-M4 MCU",
    "category": "Microcontrollers",
    "family": "STM32F4",
    "unit_price": "8.52",
    "stock_quantity": 15000,
    "lead_time_days": 12,
}


@pytest.mark.asyncio
async def test_create_product(client):
    response = await client.post("/api/v1/products", json=PRODUCT_DATA)
    assert response.status_code == 201
    data = response.json()
    assert data["part_number"] == "STM32F407VGT6"
    assert data["name"] == "STM32F407 MCU"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_products(client):
    await client.post("/api/v1/products", json=PRODUCT_DATA)
    response = await client.get("/api/v1/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_product(client):
    create_resp = await client.post("/api/v1/products", json=PRODUCT_DATA)
    product_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["part_number"] == "STM32F407VGT6"


@pytest.mark.asyncio
async def test_update_product(client):
    create_resp = await client.post("/api/v1/products", json=PRODUCT_DATA)
    product_id = create_resp.json()["id"]
    response = await client.put(f"/api/v1/products/{product_id}", json={"name": "Updated MCU"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated MCU"


@pytest.mark.asyncio
async def test_delete_product(client):
    create_resp = await client.post("/api/v1/products", json=PRODUCT_DATA)
    product_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_filter_products_by_category(client):
    await client.post("/api/v1/products", json=PRODUCT_DATA)
    response = await client.get("/api/v1/products", params={"category": "Microcontrollers"})
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await client.get("/api/v1/products", params={"category": "Sensors"})
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_search_products(client):
    await client.post("/api/v1/products", json=PRODUCT_DATA)
    response = await client.get("/api/v1/products", params={"search": "STM32"})
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_product_not_found(client):
    response = await client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
