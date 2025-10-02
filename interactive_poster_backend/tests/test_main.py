import pytest
from httpx import AsyncClient, ASGITransport
from interactive_poster_backend.main import app

@pytest.mark.asyncio
async def test_read_root():
    """
    Test that the root endpoint returns a 200 OK status code
    and the expected welcome message.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to the Interactive Poster Generator API!",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }