"""Standalone MCP server wrapping the ST Micro Orders REST API."""
import os

import httpx
from mcp.server.fastmcp import FastMCP

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

mcp = FastMCP("ST Micro Orders", instructions="Manage ST Microelectronics semiconductor orders, customers, and products.")


def _api_url(path: str) -> str:
    return f"{API_BASE_URL}{path}"


@mcp.tool()
async def list_products(category: str | None = None, family: str | None = None, search: str | None = None) -> str:
    """List ST Micro semiconductor products. Filter by category, product family, or search term."""
    params = {}
    if category:
        params["category"] = category
    if family:
        params["family"] = family
    if search:
        params["search"] = search
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api_url("/api/v1/products"), params=params)
        resp.raise_for_status()
        return resp.text


@mcp.tool()
async def get_product(product_id: str) -> str:
    """Get details of a specific product by its ID."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api_url(f"/api/v1/products/{product_id}"))
        resp.raise_for_status()
        return resp.text


@mcp.tool()
async def list_customers(search: str | None = None, country: str | None = None) -> str:
    """List customers. Filter by search term or country."""
    params = {}
    if search:
        params["search"] = search
    if country:
        params["country"] = country
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api_url("/api/v1/customers"), params=params)
        resp.raise_for_status()
        return resp.text


@mcp.tool()
async def get_customer(customer_id: str) -> str:
    """Get details of a specific customer by their ID."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api_url(f"/api/v1/customers/{customer_id}"))
        resp.raise_for_status()
        return resp.text


@mcp.tool()
async def list_orders(status: str | None = None, customer_id: str | None = None) -> str:
    """List orders. Filter by status (pending/confirmed/processing/shipped/delivered/cancelled) or customer_id."""
    params = {}
    if status:
        params["status"] = status
    if customer_id:
        params["customer_id"] = customer_id
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api_url("/api/v1/orders"), params=params)
        resp.raise_for_status()
        return resp.text


@mcp.tool()
async def get_order(order_id: str) -> str:
    """Get details of a specific order by its ID, including line items."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(_api_url(f"/api/v1/orders/{order_id}"))
        resp.raise_for_status()
        return resp.text


@mcp.tool()
async def create_order(customer_id: str, items: list[dict], shipping_address: str | None = None, notes: str | None = None) -> str:
    """Create a new order. Items should be a list of dicts with 'product_id' and 'quantity' keys."""
    payload = {
        "customer_id": customer_id,
        "items": items,
    }
    if shipping_address:
        payload["shipping_address"] = shipping_address
    if notes:
        payload["notes"] = notes
    async with httpx.AsyncClient() as client:
        resp = await client.post(_api_url("/api/v1/orders"), json=payload)
        resp.raise_for_status()
        return resp.text


@mcp.tool()
async def update_order_status(order_id: str, status: str) -> str:
    """Update an order's status. Valid statuses: pending, confirmed, processing, shipped, delivered, cancelled."""
    async with httpx.AsyncClient() as client:
        resp = await client.put(_api_url(f"/api/v1/orders/{order_id}"), json={"status": status})
        resp.raise_for_status()
        return resp.text


if __name__ == "__main__":
    mcp.run()
