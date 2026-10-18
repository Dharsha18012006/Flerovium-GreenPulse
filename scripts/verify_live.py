"""Exercise actual deployed inference on the first held-out image of each class."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.request

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--port',type=int,default=8002);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();rows=json.loads(a.manifest.read_text());results=[]
    for label in ['early_blight','healthy','late_blight']:
        row=next(r for r in rows if r['split']=='test' and r['label']==label)
        raw=(a.root/row['path']).read_bytes();start=time.perf_counter()
        request=urllib.request.Request(f'http://172.17.0.2:{a.port}/api/predict?lang=ta',data=raw,headers={'Content-Type':'image/jpeg','Host':'localhost'})
        with urllib.request.urlopen(request,timeout=60) as response:prediction=json.load(response)
        if prediction.get('architecture')!='s390x':raise ValueError('Inference not executed on s390x')
        results.append({'expected':label,'image_sha256':hashlib.sha256(raw).hexdigest(),'latency_seconds':time.perf_counter()-start,'response':prediction})
    evidence={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'selection':'First test image per class in frozen manifest, no cherry-picking','results':results}
    with a.out.open('x',encoding='utf-8') as f:json.dump(evidence,f,indent=2,ensure_ascii=False)
    print(json.dumps(evidence,indent=2,ensure_ascii=False))
