import asyncio
from io import BytesIO
import httpx
from PIL import Image
import app.main as main

def test_workflows(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DB',tmp_path/'app.sqlite3')
    async def exercise():
        async with main.lifespan(main.app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app),base_url='http://testserver') as client:
                assert (await client.get('/')).status_code==200
                assert (await client.get('/api/posts')).json()==[]
                assert (await client.post('/api/posts',json={'author':'Gardener','body':'How should I water?'})).status_code==201
                assert (await client.get('/api/posts')).json()[0]['body']=='How should I water?'
                assert (await client.post('/api/posts',json={'author':' ','body':'x'})).status_code==422
                assert (await client.post('/api/posts',json={'author':'A','body':'x'},headers={'Origin':'https://evil.example'})).status_code==403
                listing={'title':'Basil seedling','description':'Locally grown','price':25,'area':'Chennai','contact':''}
                assert (await client.post('/api/listings',json=listing)).status_code==201
                assert (await client.get('/api/listings')).json()[0]['price']==25
                assert (await client.post('/api/listings',json={**listing,'price':-1})).status_code==422
                for label in ['healthy','early_blight','late_blight']:
                    for lang in ['en','ta']:
                        data=(await client.get(f'/api/care/{label}?lang={lang}')).json()
                        assert len(data['steps'])>=2 and data['source'].startswith('https://')
                assert (await client.get('/api/care/unknown')).status_code==404
                report={'area':'Chennai South','condition':'early_blight','consent':True}
                assert (await client.post('/api/reports',json={**report,'consent':False})).status_code==422
                assert (await client.post('/api/reports',json={**report,'latitude':13.2})).status_code==422
                for _ in range(4):assert (await client.post('/api/reports',json=report)).status_code==201
                assert (await client.get('/api/signals')).json()['signals']==[]
                await client.post('/api/reports',json=report)
                assert (await client.get('/api/signals')).json()['signals'][0]['reports']==5
                with main.db() as db:db.execute("UPDATE reports SET created=datetime('now','-8 days')")
                assert (await client.get('/api/signals')).json()['signals']==[]
                assert (await client.post('/api/predict',content=b'bad',headers={'Content-Type':'image/jpeg'})).status_code==422
                assert (await client.post('/api/predict',content=b'x'*(5*1024*1024+1))).status_code==413
                image=BytesIO();Image.new('RGB',(64,64),'green').save(image,format='PNG')
                monkeypatch.setattr(main.platform,'machine',lambda:'AMD64')
                unavailable=await client.post('/api/predict',content=image.getvalue(),headers={'Content-Type':'image/png'})
                assert unavailable.status_code==503 and 'LinuxONE' in unavailable.json()['detail']
        # Reopen lifespan to verify persistence, not merely process memory.
        async with main.lifespan(main.app):
            assert len(main.posts())==1 and len(main.listings())==1
    asyncio.run(exercise())
