"""QualityLab: lightweight QA management and sample commerce SUT API."""
from __future__ import annotations
import os
import sqlite3
import json
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from .shop import CATALOG, ShopError, quote_order

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.getenv('QUALITYLAB_DB', str(ROOT / 'data' / 'qualitylab.sqlite3')))
DB.parent.mkdir(parents=True, exist_ok=True)
app = FastAPI(title='QualityLab API', version='1.0.0')

CASES = [
 ('TC-001','Inicio de sesión con credenciales válidas','Autenticación','Crítico','Automatizado','Pasó'),
 ('TC-002','Rechazo de contraseñas incorrectas','Autenticación','Alto','Automatizado','Pasó'),
 ('TC-003','Consulta del catálogo disponible','Catálogo','Alto','Automatizado','Pasó'),
 ('TC-004','Agregar productos al carrito','Carrito','Crítico','Automatizado','Pasó'),
 ('TC-005','Aplicar cupón de bienvenida','Checkout','Medio','Automatizado','Pasó'),
 ('TC-006','Bloquear pedidos sin stock','Checkout','Crítico','Automatizado','Pasó'),
 ('TC-007','Validación de dirección de entrega','Checkout','Alto','Manual','Falló'),
 ('TC-008','Procesar pago con tarjeta','Pagos','Crítico','Manual','Bloqueado'),
 ('TC-009','Visualizar historial de pedidos','Cuenta','Medio','Manual','Pasó'),
 ('TC-010','Editar cantidad del carrito','Carrito','Medio','Automatizado','Pasó'),
 ('TC-011','Comprobar diseño responsive','Interfaz','Medio','Manual','Pendiente'),
 ('TC-012','Reintentar transacción interrumpida','Pagos','Alto','Manual','Pendiente'),
]
DEFECTS = [
 ('BUG-104','El descuento se pierde al volver al checkout','Checkout','Alta','En progreso','Lucía M.','TC-005'),
 ('BUG-102','La validación del código postal permite letras','Checkout','Alta','Abierto','Mateo R.','TC-007'),
 ('BUG-099','El botón de pago no muestra estado de carga','Pagos','Media','Abierto','Renata C.','TC-008'),
 ('BUG-097','La tabla de pedidos desborda en móvil','Interfaz','Media','En revisión','Lucía M.','TC-011'),
 ('BUG-093','El mensaje de cupón expirado no se visualiza','Checkout','Baja','Resuelto','Mateo R.','TC-005'),
]

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with closing(connect()) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS cases(id TEXT PRIMARY KEY, title TEXT, area TEXT, priority TEXT, kind TEXT, status TEXT);
        CREATE TABLE IF NOT EXISTS defects(id TEXT PRIMARY KEY, title TEXT, area TEXT, severity TEXT, status TEXT, owner TEXT, case_id TEXT);
        CREATE TABLE IF NOT EXISTS runs(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, passed INTEGER, failed INTEGER, total INTEGER, created_at TEXT);
        ''')
        if not db.execute('SELECT 1 FROM cases LIMIT 1').fetchone():
            db.executemany('INSERT INTO cases VALUES(?,?,?,?,?,?)', CASES)
        if not db.execute('SELECT 1 FROM defects LIMIT 1').fetchone():
            db.executemany('INSERT INTO defects VALUES(?,?,?,?,?,?,?)', DEFECTS)
        if not db.execute('SELECT 1 FROM runs LIMIT 1').fetchone():
            db.executemany('INSERT INTO runs(name, passed, failed, total, created_at) VALUES(?,?,?,?,?)', [
              ('Regresión · Sprint 12',42,3,45,'2026-11-11T09:18:00'),
              ('Smoke · Release 1.8',18,0,18,'2026-11-10T16:42:00'),
              ('Regresión · Sprint 11',39,5,44,'2026-11-08T11:31:00'),
              ('Smoke · Release 1.7',17,1,18,'2026-11-05T15:12:00'),
            ])
        db.commit()

init_db()

@app.get('/')
def home():
    return FileResponse(ROOT/'web'/'index.html')

@app.get('/assets/{name}')
def static_file(name: str):
    if name not in ('app.css','app.js'):
        raise HTTPException(404, 'Not found')
    return FileResponse(ROOT/'web'/name)

@app.get('/api/overview')
def overview():
    with closing(connect()) as db:
        cases = [dict(row) for row in db.execute('SELECT * FROM cases ORDER BY id')]
        defects = [dict(row) for row in db.execute('SELECT * FROM defects ORDER BY id DESC')]
        runs = [dict(row) for row in db.execute('SELECT * FROM runs ORDER BY id DESC')]
    return {'project':'Comercio Nova · Storefront', 'cases':cases, 'defects':defects, 'runs':runs,
       'metrics': {'coverage': 88, 'passRate': 93.3, 'automated': 68, 'criticalBugs': sum(x['severity']=='Alta' and x['status']!='Resuelto' for x in defects)},
       'trend': [72,79,75,84,87,89,93], 'modules': [
        {'name':'Checkout', 'passed':24, 'total':28}, {'name':'Catálogo','passed':18,'total':19},
        {'name':'Autenticación','passed':17,'total':17},{'name':'Carrito','passed':14,'total':15},{'name':'Pagos','passed':8,'total':11}],
       'recentActivities': [
        {'title':'Nueva ejecución de regresión','detail':'42 de 45 casos aprobados','time':'09:18','kind':'run'},
        {'title':'BUG-104 cambiado a En progreso','detail':'Lucía M. · Checkout','time':'08:46','kind':'bug'},
        {'title':'TC-007 marcado como Falló','detail':'Validación de dirección','time':'Ayer','kind':'case'},
       ]}

class DefectCreate(BaseModel):
    title: str = Field(min_length=5, max_length=180)
    area: str = Field(default='General', max_length=60)
    severity: str = Field(default='Media', pattern='^(Alta|Media|Baja)$')

@app.post('/api/defects',status_code=201)
def create_defect(payload: DefectCreate):
    with closing(connect()) as db:
        current = db.execute('SELECT id FROM defects ORDER BY id DESC LIMIT 1').fetchone()
        number = (int(current['id'].split('-')[1]) + 1) if current else 100
        bid = f'BUG-{number:03d}'
        db.execute('INSERT INTO defects VALUES(?,?,?,?,?,?,?)',(bid,payload.title,payload.area,payload.severity,'Abierto','Sin asignar','—'))
        db.commit()
    return {'id':bid,'status':'Abierto'}

@app.patch('/api/defects/{bug_id}')
def update_defect(bug_id: str, status: str):
    if status not in ('Abierto','En progreso','En revisión','Resuelto'):
        raise HTTPException(422,'Estado no válido')
    with closing(connect()) as db:
        cur=db.execute('UPDATE defects SET status=? WHERE id=?',(status,bug_id))
        db.commit()
        if cur.rowcount==0: raise HTTPException(404,'Bug no encontrado')
    return {'id':bug_id,'status':status}

@app.get('/api/shop/products')
def products(): return [{'sku':k, **v} for k,v in CATALOG.items()]

class Checkout(BaseModel):
    sku: str
    quantity: int
    coupon: str = ''

@app.post('/api/shop/quote')
def quote(payload: Checkout):
    try: return quote_order(payload.sku,payload.quantity,payload.coupon)
    except ShopError as exc: raise HTTPException(422,str(exc))

@app.post('/api/runs')
def execute_smoke():
    checks = [
        ('Catálogo accesible',lambda: len(CATALOG)>=3),
        ('Subtotal correcto',lambda: quote_order('SKU-104',2)['total']==179.8),
        ('Descuento de bienvenida',lambda: quote_order('SKU-104',2,'BIENVENIDO10')['total']==161.82),
        ('Validación de inventario',lambda: _raises('SKU-205',24)),
        ('Validación de cantidad',lambda: _raises('SKU-104',0)),
        ('Rechazo de cupones inválidos',lambda: _raises('SKU-104',1,'INVALIDO')),
    ]
    results=[{'name':name,'passed':bool(fn())} for name,fn in checks]
    passed=sum(r['passed'] for r in results)
    with closing(connect()) as db:
        db.execute('INSERT INTO runs(name,passed,failed,total,created_at) VALUES(?,?,?,?,?)',('Smoke · Ejecución local',passed,len(results)-passed,len(results),datetime.now(timezone.utc).isoformat()))
        db.commit()
    return {'results':results,'passed':passed,'failed':len(results)-passed}

def _raises(*args):
    try: quote_order(*args)
    except ShopError: return True
    return False

@app.get('/health')
def health(): return {'status':'ok'}
