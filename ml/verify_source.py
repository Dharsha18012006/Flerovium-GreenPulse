"""Verify existing image bytes against original Git tree and original leaf metadata.

Downloads public metadata only. Keeps all raw data; creates a verified audit subset.
Unmapped or ambiguous physical leaf IDs are excluded from this training run.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request

REPO='https://api.github.com/repos/spMohanty/PlantVillage-Dataset'
MAP='https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/master/leaf-map.json'
CLASS={'early_blight':'Tomato___Early_blight','healthy':'Tomato___healthy','late_blight':'Tomato___Late_blight'}

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'GreenPulse-Datathon-provenance-audit'})
    with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)

def verify(root,audit_dir,out):
    commit='7f7ecc7e1eaca78107e3affe7cb5abd9427e139a' # pinned dataset revision
    tree=get(REPO+'/git/trees/'+commit)['tree']
    for part in ['raw','color']:
        sha=next(item['sha'] for item in tree if item['path']==part)
        tree=get(REPO+'/git/trees/'+sha)['tree']
    upstream={}
    for label,folder in CLASS.items():
        sha=next(item['sha'] for item in tree if item['path']==folder)
        upstream[label]={item['path']:item['sha'] for item in get(REPO+'/git/trees/'+sha)['tree'] if item['type']=='blob'}
    # Pin leaf map to the same commit as the source-image trees.
    mapping_url=f'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/{commit}/leaf-map.json'
    leafmap=get(mapping_url)
    rows=json.loads((audit_dir/'manifest.json').read_text())
    accepted=[];excluded=[];groups={};mismatches=[]
    for row in rows:
        path=(root/row['path']).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('Path outside dataset')
        raw=path.read_bytes()
        gitsha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if hashlib.sha256(raw).hexdigest()!=row['sha256'] or upstream[row['label']].get(path.name)!=gitsha:
            mismatches.append(row['path']);continue
        key=path.stem.split('___')[-1].lower()
        leaf=leafmap.get(key,[])
        if len(leaf)!=1 or not leaf[0].startswith(CLASS[row['label']]+':::'):
            excluded.append({'path':row['path'],'reason':'Missing or ambiguous original physical leaf ID'});continue
        groups[row['path']]=leaf[0]
        accepted.append(row)
    if mismatches:raise ValueError(f'{len(mismatches)} files do not match the original repository; stop and investigate')
    out.mkdir(parents=True,exist_ok=False)
    report=json.loads((audit_dir/'audit.json').read_text())
    paths={r['path'] for r in accepted}
    report['valid_images']=len(accepted)
    report['class_counts']=dict(Counter(r['label'] for r in accepted))
    report['near_duplicate_candidates']=[pair for pair in report['near_duplicate_candidates'] if set(pair)<=paths]
    report['note']='Verified subset only; all original images preserved. See source_verification.json for exclusions.'
    for name,value in [('manifest',accepted),('audit',report),('verified-leaf-groups',groups)]:
        (out/(name+'.json')).write_text(json.dumps(value,indent=2))
    provenance={'verified':True,'source_url':'https://github.com/spMohanty/PlantVillage-Dataset','source_commit':commit,
       'license':'CC BY-SA 3.0','license_url':'https://huggingface.co/datasets/mohanty/PlantVillage/blob/main/README.md',
       'verified_by':'GreenPulse automated git-blob byte verification against original repository; original leaf-map IDs',
       'leaf_group_source':mapping_url,'verified_at_utc':datetime.now(timezone.utc).isoformat(),
       'original_images_byte_verified':len(rows),'accepted_images':len(accepted),'class_counts':report['class_counts'],
       'excluded_unmapped':excluded,'no_source_images_changed':True}
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2))
    (out/'source_verification.json').write_text(json.dumps(provenance,indent=2))
    print(json.dumps({k:v for k,v in provenance.items() if k!='excluded_unmapped'},indent=2))
    print('Unmapped excluded, preserved on disk:',len(excluded))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();verify(a.root,a.audit,a.out)
