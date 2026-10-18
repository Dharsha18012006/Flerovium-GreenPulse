from contextlib import asynccontextmanager, contextmanager
from pathlib import Path
import os
import platform
import sqlite3
import re

from fastapi import FastAPI, HTTPException, Request, Query
from starlette.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, ConfigDict, model_validator, StrictBool
from typing import Literal, Annotated
from app.care import CARE, get_guidance
from ml.inference import LeafClassifier, InvalidImage, ModelUnavailable

ROOT = Path(__file__).resolve().parent.parent
DB = Path(os.getenv('GREENPULSE_DB', str(ROOT / 'data/app.sqlite3')))
MODEL_DIR = Path(os.getenv('GREENPULSE_MODEL_DIR', str(ROOT / 'artifacts/model-svm')))
classifier = LeafClassifier(MODEL_DIR)

@contextmanager
def db():
    con = sqlite3.connect(DB, timeout=10)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

@asynccontextmanager
async def lifespan(app):
    DB.parent.mkdir(parents=True, exist_ok=True)
    with db() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY, author TEXT, body TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS listings(id INTEGER PRIMARY KEY, title TEXT, description TEXT, price INTEGER, area TEXT, contact TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, area TEXT, condition TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
        ''')
        # Additive, idempotent migration: retain every existing listing/report.
        for table, column, definition in [('listings','category',"TEXT NOT NULL DEFAULT 'Other'"),('reports','simulated','INTEGER NOT NULL DEFAULT 0'),('listings','seller_email',"TEXT NOT NULL DEFAULT ''"),('listings','contact_consent','INTEGER NOT NULL DEFAULT 0')]:
            if column not in {row[1] for row in con.execute(f'PRAGMA table_info({table})')}:
                con.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
    yield

app = FastAPI(title='GreenPulse', lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost', '127.0.0.1', 'testserver'])

@app.middleware('http')
async def local_only_writes(request: Request, call_next):
    # No browser cross-origin writes to the private, tunnel-accessed prototype.
    origin = request.headers.get('origin')
    if request.method == 'POST' and origin and origin != str(request.base_url).rstrip('/'):
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail': 'Cross-origin writes are disabled'}, status_code=403)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

@app.get('/api/health')
def health():
    return {'status': 'ok', 'architecture': platform.machine(), 'model_file_present': any((MODEL_DIR/name).exists() for name in ['model.keras','model.joblib']), 'inference_loaded': classifier.model is not None, 'mode': 'private prototype'}

@app.get('/api/care/{condition}')
def care(condition: str, lang: Literal['en','ta']='en'):
    if condition not in CARE:
        raise HTTPException(404, 'Unsupported condition')
    return get_guidance(condition, lang)

@app.post('/api/predict')
async def predict(request: Request, lang: Literal['en','ta']='en'):
    # Raw streamed body avoids multipart's temporary-file spooling.
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw)+len(chunk)>5*1024*1024:
            raise HTTPException(413, 'Use an image smaller than 5 MB')
        raw.extend(chunk)
    return await run_in_threadpool(predict_image, raw, lang)

def classify_image(raw):
    try:
        return classifier.predict_bytes(raw)
    except InvalidImage as exc:
        raise HTTPException(422, str(exc)) from exc
    except ModelUnavailable as exc:
        raise HTTPException(503, str(exc)) from exc

def predict_image(raw, lang):
    result = classify_image(raw)
    # Presentation-only care stays separate from the model's prediction function.
    return {**result, 'guidance': care(result['label'],lang) if not result['uncertain'] else None}

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class Post(StrictModel):
    author: str = Field(default='Anonymous gardener',min_length=1,max_length=40)
    body: str = Field(min_length=1,max_length=1000)

Category = Literal['Plants','Seeds','Tools','Pots','Soil and compost','Other']

class Listing(StrictModel):
    title: str = Field(min_length=2,max_length=80)
    description: str = Field(min_length=1,max_length=500)
    price: int | None = Field(default=None,ge=0,le=1000000,strict=True)
    category: Category = 'Other'
    area: str = Field(min_length=2,max_length=60)
    contact: str = Field(default='',max_length=120)  # Legacy input never published.
    seller_email: str = Field(default='',max_length=120)
    contact_consent: StrictBool = False

    @model_validator(mode='after')
    def validate_public_contact(self):
        if self.contact:
            raise ValueError('Use the optional seller email and explicit sharing consent.')
        if bool(self.seller_email) != self.contact_consent:
            raise ValueError('An email and explicit sharing consent are both required to share contact details.')
        if self.seller_email and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._%+\-]*@[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?)+", self.seller_email):
            raise ValueError('Enter a valid plain email address, without links or message headers.')
        return self

class Report(StrictModel):
    area: Literal['Chennai North','Chennai South','Chennai Central','Other urban gardens']
    condition: Literal['healthy','early_blight','late_blight']
    consent: Literal[True]
    simulated: bool = False

@app.get('/api/posts')
def posts():
    with db() as con:
        return [dict(r) for r in con.execute('SELECT * FROM posts ORDER BY id DESC LIMIT 100')]

@app.post('/api/posts', status_code=201)
def add_post(post: Post):
    with db() as con:
        cur = con.execute('INSERT INTO posts(author,body) VALUES(?,?)',(post.author,post.body))
        return {'id': cur.lastrowid}

@app.get('/api/listings')
def listings(q: Annotated[str, Query(max_length=100)] = '', category: Category | None = None):
    with db() as con:
        return [dict(r) for r in con.execute(
            "SELECT id,title,description,price,area,category,created,'' AS contact,contact_consent,CASE WHEN contact_consent=1 THEN seller_email ELSE '' END AS seller_email FROM listings WHERE (? IS NULL OR category=?) AND instr(lower(title || ' ' || description || ' ' || area),lower(?)) > 0 ORDER BY id DESC LIMIT 100",
            (category,category,q.strip()))]

@app.post('/api/listings', status_code=201)
def add_listing(item: Listing):
    with db() as con:
        cur = con.execute('INSERT INTO listings(title,description,price,area,contact,category,seller_email,contact_consent) VALUES(?,?,?,?,?,?,?,?)',(item.title,item.description,item.price,item.area,'',item.category,item.seller_email,int(item.contact_consent)))
        return {'id': cur.lastrowid}

@app.post('/api/reports', status_code=201)
def report(item: Report):
    with db() as con:
        con.execute('DELETE FROM reports WHERE created < datetime(\'now\',\'-7 days\')')
        con.execute('INSERT INTO reports(area,condition,simulated) VALUES(?,?,?)',(item.area,item.condition,int(item.simulated)))
    return {'saved': True, 'retention_days': 7, 'notice': 'Unverified self-report; no image, exact location, or identity saved.'}

@app.get('/api/signals')
def signals():
    with db() as con:
        rows = con.execute("SELECT area,condition,simulated,count(*) AS reports,date(min(created)) AS first_date,date(max(created)) AS last_date FROM reports WHERE created >= datetime('now','-7 days') GROUP BY area,condition,simulated HAVING count(*) >= 5").fetchall()
    return {'signals': [dict(r) for r in rows], 'minimum_reports': 5, 'window_days':7, 'timezone':'UTC',
            'notice': 'Unverified submissions over 7 days, not unique gardens or outbreak predictions. Small groups are hidden; repeat reports can inflate counts.'}

app.mount('/static', StaticFiles(directory=ROOT/'app/static'), name='static')

@app.get('/')
def home():
    return FileResponse(ROOT/'app/static/index.html')
