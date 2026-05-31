import os
import pytest
import httpx

BASE_URL = os.getenv("SERVICE_URL", "http://localhost:8080")


@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=60.0)


@pytest.fixture(autouse=True)
def cleanup(client):
    yield
    client.delete("/users/test-contract-user")
    client.delete("/users/test-session-user-a")
    client.delete("/users/test-session-user-b")
    client.delete("/users/fixture-user")
