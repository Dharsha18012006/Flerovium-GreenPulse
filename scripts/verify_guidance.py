"""Verify curated care against actual LinuxONE responses via the private tunnel."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--url',default='http://127.0.0.1:8003')
    p.add_argument('--images',type=Path,default=Path('artifacts/evidence/demo-leaves'))
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    rows=[]
    for label in ['healthy','early_blight','late_blight','uncertain']:
        raw=(args.images/(label+'.jpg')).read_bytes()
        pair=[]
        for lang in ['en','ta']:
            request=urllib.request.Request(args.url+'/api/predict?lang='+lang,data=raw,headers={'Content-Type':'image/jpeg'})
            with urllib.request.urlopen(request,timeout=45) as response: result=json.load(response)
            assert result['architecture']=='s390x'
            if label=='uncertain':
                assert result['uncertain'] and result['guidance'] is None
            else:
                assert result['label']==label and not result['uncertain']
                guidance=result['guidance']
                assert guidance['language']==lang and guidance['generated'] is False
                assert all(guidance[k] for k in ['explanation','symptoms','prevention','steps','references','scope'])
            pair.append(result)
        assert all(pair[0][key]==pair[1][key] for key in ['label','confidence','score','uncertain'])
        rows.append({'image':label,'sha256':hashlib.sha256(raw).hexdigest(),'responses':pair})
    with args.out.open('x',encoding='utf-8') as stream:
        json.dump({'timestamp_utc':datetime.now(timezone.utc).isoformat(),'url':args.url,'results':rows},stream,indent=2,ensure_ascii=False)
    print('Verified 8 real s390x predictions: 3 supported classes plus an uncertain leaf, each in English/Tamil.')

if __name__=='__main__':main()
