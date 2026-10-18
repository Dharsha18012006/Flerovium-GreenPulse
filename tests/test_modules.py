import asyncio
import sqlite3
import httpx
from app import main


def test_additive_migration_and_market_search(tmp_path,monkeypatch):
    path=tmp_path/'legacy.sqlite3'
    with sqlite3.connect(path) as db:
        db.executescript("CREATE TABLE listings(id INTEGER PRIMARY KEY,title TEXT,description TEXT,price INTEGER,area TEXT,contact TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE reports(id INTEGER PRIMARY KEY,area TEXT,condition TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP);")
        db.execute('INSERT INTO listings(title,description,price,area,contact) VALUES(?,?,?,?,?)',('Legacy pot','Keep existing record',12,'Chennai','Existing note'))
    monkeypatch.setattr(main,'DB',path)
    async def check():
        async with main.lifespan(main.app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),base_url='http://testserver') as client:
                old=(await client.get('/api/listings')).json()[0]
                assert old['contact']=='' and old['seller_email']=='' and old['contact_consent']==0
                assert old['title']=='Legacy pot' and old['category']=='Other' and old['price']==12
                item={'title':'TEST basil seeds','description':'Demo only','category':'Seeds','area':'Chennai South'}
                assert (await client.post('/api/listings',json=item)).status_code==201
                found=(await client.get('/api/listings',params={'q':'BASIL','category':'Seeds'})).json()
                assert len(found)==1 and found[0]['price'] is None and found[0]['contact']==''
                assert (await client.get('/api/listings',params={'q':'South'})).json()[0]['category']=='Seeds'
                for query in ["' OR 1=1 --",'%','nonexistent']:
                    assert (await client.get('/api/listings',params={'q':query})).json()==[]
                assert (await client.get('/api/listings?category=Invalid')).status_code==422
                for changes in [{'category':'Invalid'},{'price':-1},{'price':1.5},{'price':True},{'title':'  '},{'area':' '}]:
                    assert (await client.post('/api/listings',json={**item,**changes})).status_code==422
                assert (await client.get('/api/listings',params={'q':'x'*101})).status_code==422
        # Restart/migration is idempotent and retains both original and new data.
        async with main.lifespan(main.app):
            assert len(main.listings())==2
    asyncio.run(check())


def test_report_dates_and_simulation_separation(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DB',tmp_path/'signals.sqlite3')
    async def check():
        async with main.lifespan(main.app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),base_url='http://testserver') as client:
                assert (await client.get('/api/signals')).json()['signals']==[]
                report={'area':'Chennai South','condition':'early_blight','consent':True}
                for _ in range(4):await client.post('/api/reports',json={**report,'simulated':True})
                await client.post('/api/reports',json=report)
                assert (await client.get('/api/signals')).json()['signals']==[]
                await client.post('/api/reports',json={**report,'simulated':True})
                signals=(await client.get('/api/signals')).json()['signals']
                assert len(signals)==1 and signals[0]['simulated']==1 and signals[0]['reports']==5
                assert len(signals[0]['first_date'])==10 and signals[0]['first_date']==signals[0]['last_date']
                assert 'latitude' not in signals[0] and 'author' not in signals[0]
                for _ in range(4):await client.post('/api/reports',json=report)
                signals=(await client.get('/api/signals')).json()['signals']
                assert len(signals)==2 and all(s['reports']==5 for s in signals)
                assert (await client.post('/api/reports',json={**report,'consent':False})).status_code==422
    asyncio.run(check())


def test_anonymous_posts_validate_and_persist(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DB',tmp_path/'community.sqlite3')
    async def check():
        async with main.lifespan(main.app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),base_url='http://testserver') as client:
                assert (await client.get('/api/posts')).json()==[]
                assert (await client.post('/api/posts',json={'body':'How do I support tomato plants?'})).status_code==201
                for body in ['', ' ', 'x'*1001]:
                    assert (await client.post('/api/posts',json={'body':body})).status_code==422
                post=(await client.get('/api/posts')).json()[0]
                assert post['author']=='Anonymous gardener' and post['created']
        async with main.lifespan(main.app):assert len(main.posts())==1
    asyncio.run(check())


def test_seller_contact_requires_consent_and_is_safe(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DB',tmp_path/'contacts.sqlite3')
    async def check():
        async with main.lifespan(main.app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),base_url='http://testserver') as client:
                item={'title':'DEMO contact test','description':'Not a real seller','area':'Test area'}
                for changes in [
                    {'seller_email':'seller@example.invalid'},
                    {'contact_consent':True},
                    {'seller_email':'bad address','contact_consent':True},
                    {'seller_email':'seller@example.invalid?subject=bad','contact_consent':True},
                    {'seller_email':'seller@example.invalid\r\nBcc:other@example.invalid','contact_consent':True},
                    {'seller_email':'<script>@example.invalid','contact_consent':True},
                    {'seller_email':'seller@example.invalid','contact_consent':'true'},
                    {'contact':'legacy private note'},
                ]:
                    assert (await client.post('/api/listings',json={**item,**changes})).status_code==422
                assert (await client.post('/api/listings',json=item)).status_code==201
                public={**item,'seller_email':'seller@example.invalid','contact_consent':True}
                assert (await client.post('/api/listings',json=public)).status_code==201
                rows=(await client.get('/api/listings')).json()
                assert rows[0]['seller_email']=='seller@example.invalid' and rows[0]['contact_consent']==1
                assert rows[1]['seller_email']=='' and rows[1]['contact_consent']==0
        async with main.lifespan(main.app):
            assert main.listings()[0]['seller_email']=='seller@example.invalid'
    asyncio.run(check())
