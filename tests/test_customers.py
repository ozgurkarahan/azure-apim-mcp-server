import pytest


CUSTOMER_DATA = {
    "company_name": "TechFusion GmbH",
    "contact_name": "Klaus Weber",
    "contact_email": "k.weber@techfusion.de",
    "phone": "+49-89-555-0101",
    "address": "Maximilianstraße 35",
    "city": "Munich",
    "country": "Germany",
}


@pytest.mark.asyncio
async def test_create_customer(client):
    response = await client.post("/api/v1/customers", json=CUSTOMER_DATA)
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == "TechFusion GmbH"
    assert data["country"] == "Germany"


@pytest.mark.asyncio
async def test_list_customers(client):
    await client.post("/api/v1/customers", json=CUSTOMER_DATA)
    response = await client.get("/api/v1/customers")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_customer(client):
    create_resp = await client.post("/api/v1/customers", json=CUSTOMER_DATA)
    customer_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/customers/{customer_id}")
    assert response.status_code == 200
    assert response.json()["company_name"] == "TechFusion GmbH"


@pytest.mark.asyncio
async def test_update_customer(client):
    create_resp = await client.post("/api/v1/customers", json=CUSTOMER_DATA)
    customer_id = create_resp.json()["id"]
    response = await client.put(f"/api/v1/customers/{customer_id}", json={"company_name": "TechFusion AG"})
    assert response.status_code == 200
    assert response.json()["company_name"] == "TechFusion AG"


@pytest.mark.asyncio
async def test_filter_customers_by_country(client):
    await client.post("/api/v1/customers", json=CUSTOMER_DATA)
    response = await client.get("/api/v1/customers", params={"country": "Germany"})
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_search_customers(client):
    await client.post("/api/v1/customers", json=CUSTOMER_DATA)
    response = await client.get("/api/v1/customers", params={"search": "TechFusion"})
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_customer_not_found(client):
    response = await client.get("/api/v1/customers/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
