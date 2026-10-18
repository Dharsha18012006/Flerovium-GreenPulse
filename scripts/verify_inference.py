"""Capture one real LinuxONE inference response and its image checksum.

Use a known held-out image; output contains no original image or exact location.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--image',type=Path,required=True);p.add_argument('--port',type=int,default=8000);p.add_argument('--host',choices=['127.0.0.1','172.17.0.2'],default='127.0.0.1');p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();raw=a.image.read_bytes()
    if len(raw)>5*1024*1024:raise ValueError('Image exceeds upload limit')
    req=urllib.request.Request(f'http://{a.host}:{a.port}/api/predict',data=raw,headers={'Content-Type':'application/octet-stream','Host':'localhost'})
    with urllib.request.urlopen(req,timeout=60) as r:result=json.load(r)
    if result.get('architecture')!='s390x':raise ValueError('Not LinuxONE inference')
    evidence={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'image_sha256':hashlib.sha256(raw).hexdigest(),'response':result}
    with a.out.open('x',encoding='utf-8') as f:json.dump(evidence,f,indent=2)
    print(json.dumps(evidence,indent=2))
