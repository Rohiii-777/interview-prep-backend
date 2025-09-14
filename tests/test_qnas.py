import pytest
from httpx import AsyncClient
from app import app

@pytest.mark.asyncio
async def test_create_qna():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # ensure category exists first
        await ac.post("/categories/", json={"name": "SQL"})

        res = await ac.post("/qnas/", json={
            "question": "What is an index in SQL?",
            "answer": "It speeds up searches using B-trees.",
            "category_id": 1
        })
    assert res.status_code == 201
    data = res.json()
    assert data["question"].startswith("What is an index")

@pytest.mark.asyncio
async def test_search_qna():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        res = await ac.get("/qnas/?search=index")
    assert res.status_code == 200
    data = res.json()
    assert any("index" in q["question"].lower() for q in data)
