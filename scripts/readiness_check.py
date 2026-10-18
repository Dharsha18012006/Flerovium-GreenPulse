"""Readiness smoke checks through the private tunnel; creates labeled test records."""
import argparse
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
import statistics
import time
import urllib.request
import urllib.parse
import urllib.error
from PIL import Image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8003')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():raise SystemExit('Evidence already exists; use a new output filename.')
    checks=[]
    def request(path,data=None,expected=200,headers=None):
        body=json.dumps(data).encode() if isinstance(data,dict) else data
        h={'Content-Type':'application/json' if isinstance(data,dict) else 'image/jpeg',**(headers or {})}
        req=urllib.request.Request(args.url+path,data=body,headers=h)
        start=time.perf_counter()
        try:
            with urllib.request.urlopen(req,timeout=45) as response:
                status=response.status;content=response.read()
        except urllib.error.HTTPError as error:status=error.code;content=error.read()
        elapsed=time.perf_counter()-start
        assert status==expected,(path,status,expected)
        checks.append({'path':path,'status':status,'seconds':elapsed})
        return json.loads(content),elapsed
    health,_=request('/api/health');assert health['architecture']=='s390x'
    predictions=[];times=[]
    for name in ['early_blight','healthy','late_blight','uncertain']:
        raw=(Path('artifacts/evidence/demo-leaves')/(name+'.jpg')).read_bytes()
        for language in ['en','ta']:
            result,elapsed=request('/api/predict?lang='+language,raw)
            assert result['architecture']=='s390x'
            if name=='uncertain':assert result['uncertain'] and result['guidance'] is None
            else:assert result['label']==name and result['guidance']['language']==language
            predictions.append({'sample':name,'language':language,'response':result,'http_seconds':elapsed})
            times.append(elapsed)
    # Invalid inputs must fail predictably, followed by a successful health check.
    gif=BytesIO();Image.new('RGB',(64,64),'green').save(gif,format='GIF')
    for raw,status in [(b'',422),(b'not an image',422),(gif.getvalue(),422),(b'x'*(5*1024*1024+1),413)]:
        request('/api/predict',raw,expected=status)
    request('/api/posts',{},expected=422)
    request('/api/listings',{},expected=422)
    request('/api/reports',{'area':'Chennai North','condition':'healthy','consent':False},expected=422)
    request('/api/care/not-supported',expected=404)
    request('/api/care/healthy?lang=xx',expected=422)
    request('/api/posts',{'body':'TEST rejected cross-origin request'},expected=403,headers={'Origin':'https://example.invalid'})
    marker='READINESS DEMO '+datetime.now(timezone.utc).strftime('%H%M%S')
    post,_=request('/api/posts',{'body':marker+' — verification only, not a real observation.'},201)
    posts,_=request('/api/posts');assert any(p['id']==post['id'] and p['author']=='Anonymous gardener' for p in posts)
    listing,_=request('/api/listings',{'title':marker,'description':'DEMONSTRATION: no goods or seller offered.','category':'Tools','area':'Other urban gardens'},201)
    listings,_=request('/api/listings?q='+urllib.parse.quote(marker)+'&category=Tools')
    assert any(row['id']==listing['id'] and row['price'] is None for row in listings)
    empty,_=request('/api/listings?q=readiness-no-matches-xyz');assert empty==[]
    signals,_=request('/api/signals')
    assert all(row['reports']>=5 and row['first_date']<=row['last_date'] for row in signals['signals'])
    final_health,_=request('/api/health');assert final_health['inference_loaded']
    evidence={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'url':args.url,'health':final_health,'checks':checks,'predictions':predictions,'signals':signals,'created_test_ids':{'post':post['id'],'listing':listing['id']},'http_latency':{'requests':len(times),'median_seconds':statistics.median(times),'max_seconds':max(times),'scope':'Sequential Windows urllib requests through SSH and proxy, including upload/network/HTTP, model already warm; not model-only latency.'},'limitations':'Small sequential smoke run, not a load or uptime guarantee. Created records explicitly marked DEMO.'}
    with args.out.open('x',encoding='utf-8') as f:json.dump(evidence,f,indent=2,ensure_ascii=False)
    print(json.dumps({'passed_checks':len(checks),'health':final_health,'http_latency':evidence['http_latency']},indent=2))

if __name__=='__main__':main()
