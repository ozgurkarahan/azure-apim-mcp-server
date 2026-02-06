import pytest


CUSTOMER_DATA = {
    "company_name": "TechFusion GmbH",
    "contact_name": "Klaus Weber",
    "contact_email": "k.weber@techfusion.de",
    "country": "Germany",
}

PRODUCT_DATA = {
    "part_number": "STM32F407VGT6",
    "name": "STM32F407 MCU",
    "category": "Microcontrollers",
    "unit_price": "8.52",
    "stock_quantity": 15000,
}


async def _create_customer_and_product(client):
    cust_resp = await client.post("/api/v1/customers", json=CUSTOMER_DATA)
    prod_resp = await client.post("/api/v1/products", json=PRODUCT_DATA)
    return cust_resp.json()["id"], prod_resp.json()["id"]


@pytest.mark.asyncio
async def test_create_order(client):
    customer_id, product_id = await _create_customer_and_product(client)
    order_data = {
        "customer_id": customer_id,
        "shipping_address": "Munich, Germany",
        "items": [{"product_id": product_id, "quantity": 100}],
    }
    response = await client.post("/api/v1/orders", json=order_data)
    assert response.status_code == 201
    data = response.json()
    assert data["order_number"].startswith("ST-ORD-")
    assert data["status"] == "pending"
    assert len(data["items"]) == 1
    assert float(data["total_amount"]) == pytest.approx(852.0, rel=0.01)


@pytest.mark.asyncio
async def test_list_orders(client):
    customer_id, product_id = await _create_customer_and_product(client)
    order_data = {
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 50}],
    }
    await client.post("/api/v1/orders", json=order_data)
    response = await client.get("/api/v1/orders")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_order(client):
    customer_id, product_id = await _create_customer_and_product(client)
    order_data = {
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 50}],
    }
    create_resp = await client.post("/api/v1/orders", json=order_data)
    order_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id


@pytest.mark.asyncio
async def test_update_order_status(client):
    customer_id, product_id = await _create_customer_and_product(client)
    order_data = {
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 50}],
    }
    create_resp = await client.post("/api/v1/orders", json=order_data)
    order_id = create_resp.json()["id"]
    response = await client.put(f"/api/v1/orders/{order_id}", json={"status": "confirmed"})
    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"


@pytest.mark.asyncio
async def test_cancel_order(client):
    customer_id, product_id = await _create_customer_and_product(client)
    order_data = {
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 50}],
    }
    create_resp = await client.post("/api/v1/orders", json=order_data)
    order_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_filter_orders_by_status(client):
    customer_id, product_id = await _create_customer_and_product(client)
    order_data = {
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "quantity": 50}],
    }
    await client.post("/api/v1/orders", json=order_data)
    response = await client.get("/api/v1/orders", params={"status": "pending"})
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await client.get("/api/v1/orders", params={"status": "shipped"})
    assert response.status_code == 200
    assert len(response.json()) == 0


@pytest.mark.asyncio
async def test_order_not_found(client):
    response = await client.get("/api/v1/orders/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_order_invalid_product(client):
    cust_resp = await client.post("/api/v1/customers", json=CUSTOMER_DATA)
    customer_id = cust_resp.json()["id"]
    order_data = {
        "customer_id": customer_id,
        "items": [{"product_id": "00000000-0000-0000-0000-000000000000", "quantity": 50}],
    }
    response = await client.post("/api/v1/orders", json=order_data)
    assert response.status_code == 400
