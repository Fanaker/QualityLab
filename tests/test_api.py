import os
import tempfile
from pathlib import Path
os.environ['QUALITYLAB_DB'] = str(Path(tempfile.gettempdir())/'qualitylab_pytest.sqlite3')
from fastapi.testclient import TestClient
from app.main import app
from app.shop import quote_order, ShopError
client=TestClient(app)

def test_health_and_summary():
    assert client.get('/health').json()['status']=='ok'
    data=client.get('/api/overview').json()
    assert len(data['cases'])>=12 and data['metrics']['criticalBugs']>=1

def test_checkout_and_discount():
    r=client.post('/api/shop/quote',json={'sku':'SKU-104','quantity':2,'coupon':'BIENVENIDO10'})
    assert r.status_code==200 and r.json()['total']==161.82

def test_checkout_invalid_input():
    assert client.post('/api/shop/quote',json={'sku':'SKU-104','quantity':0}).status_code==422
    assert client.post('/api/shop/quote',json={'sku':'NOTHING','quantity':1}).status_code==422

def test_smoke_suite_runs():
    d=client.post('/api/runs').json()
    assert d['passed']==6 and d['failed']==0

def test_create_and_update_bug():
    r=client.post('/api/defects',json={'title':'El contador muestra importe negativo','area':'Carrito','severity':'Media'})
    assert r.status_code==201
    bug=r.json()['id']
    assert client.patch(f'/api/defects/{bug}?status=Resuelto').status_code==200
    assert client.patch('/api/defects/BUG-000?status=Resuelto').status_code==404
