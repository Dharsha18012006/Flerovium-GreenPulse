"""Fetch a bounded, source-verified supplemental dataset without modifying existing data.
One image per known physical leaf. Excludes all original images and known original leaf groups.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
from urllib.parse import quote
import urllib.request
from ml.verify_source import get, REPO, CLASS

def supplement(original_manifest,out,per_class):
    rows=json.loads(original_manifest.read_text())
    commit='7f7ecc7e1eaca78107e3affe7cb5abd9427e139a' # pinned dataset revision
    leafmap=get(f'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/{commit}/leaf-map.json')
    excluded_names={Path(r['path']).name for r in rows}
    excluded_groups=set()
    for r in rows:excluded_groups.update(leafmap.get(Path(r['path']).stem.split('___')[-1].lower(),[]))
    tree=get(REPO+'/git/trees/'+commit)['tree']
    for part in ['raw','color']:
        tree=get(REPO+'/git/trees/'+next(item['sha'] for item in tree if item['path']==part))['tree']
    selected=[];rng=random.Random(2047)
    for label,folder in CLASS.items():
        sha=next(item['sha'] for item in tree if item['path']==folder)
        candidates=get(REPO+'/git/trees/'+sha)['tree'];rng.shuffle(candidates)
        seen=set()
        for item in candidates:
            if item['type']!='blob' or item['path'] in excluded_names:continue
            ids=leafmap.get(Path(item['path']).stem.split('___')[-1].lower(),[])
            if len(ids)!=1 or not ids[0].startswith(folder+':::') or ids[0] in excluded_groups or ids[0] in seen:continue
            seen.add(ids[0]);selected.append({'folder':folder,'filename':item['path'],'gitsha':item['sha'],'leaf_id':ids[0]})
            if len(seen)>=per_class:break
        if len(seen)<per_class:raise ValueError(f'Insufficient mapped independent leaves for {label}: {len(seen)}')
    out.mkdir(parents=True,exist_ok=False)
    for folder in CLASS.values():(out/folder).mkdir()
    def fetch(item):
        url=f"https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/{commit}/raw/color/"+quote(item['folder']+'/'+item['filename'])
        raw=None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url,timeout=30) as response:raw=response.read()
                break
            except Exception:
                if attempt==2:raise
        actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if actual!=item['gitsha']:raise ValueError('Original image hash mismatch')
        path=out/item['folder']/item['filename'];path.write_bytes(raw)
        return {'path':path.relative_to(out).as_posix(),'leaf_id':item['leaf_id'],'sha256':hashlib.sha256(raw).hexdigest()}
    with ThreadPoolExecutor(max_workers=6) as pool:
        downloaded=[]
        for item in pool.map(fetch,selected):
            downloaded.append(item)
            if len(downloaded)%100==0:print('Verified downloads:',len(downloaded),flush=True)
    (out/'download_manifest.json').write_text(json.dumps({'source_commit':commit,'seed':2047,'images':downloaded,'excluded_original_images':len(rows),'excluded_original_leaf_groups':len(excluded_groups)},indent=2))
    print('Supplement complete; original dataset unchanged.',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--original-manifest',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--per-class',type=int,default=120)
    a=p.parse_args();supplement(a.original_manifest,a.out,a.per_class)
