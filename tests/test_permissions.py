import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_public_menu_requires_token():
    client=TestClient(app)
    r=client.get('/api/public/menu', params={'table_token':'bad'})
    assert r.status_code in (400, 404)