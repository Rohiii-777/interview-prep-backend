import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.asyncio
async def test_create_category():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.post("/categories/", json={"name": "Databases"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Databases"

@pytest.mark.asyncio
async def test_create_duplicate_category():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # try creating same category again
        res = await ac.post("/categories/", json={"name": "Databases"})
    assert res.status_code == 400
