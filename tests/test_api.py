from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_health():
    assert client.get('/health').json() == {'status':'ok'}

def test_register_login():
    email='test@example.com'
    r=client.post('/auth/register',json={'email':email,'password':'StrongPass123!'})
    assert r.status_code in (200,409)
    r=client.post('/auth/login',json={'email':email,'password':'StrongPass123!'})
    assert r.status_code==200 and 'access_token' in r.json()
