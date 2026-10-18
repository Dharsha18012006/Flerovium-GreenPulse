"""Recreate the exact frozen image set from a manifest and pinned public source.
Existing matching images are retained; mismatches abort instead of overwriting.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
import urllib.request
from ml.verify_source import CLASS

REVISION='7f7ecc7e1eaca78107e3affe7cb5abd9427e139a'

def reproduce(manifest, root, verify_only=False):
    rows=json.loads(manifest.read_text());verified=0;downloaded=0
    for row in rows:
        path=(root/row['path']).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('Manifest path outside destination')
        if row['label'] not in CLASS:raise ValueError('Unsupported label')
        if path.exists():raw=path.read_bytes()
        else:
            if verify_only:raise FileNotFoundError(path)
            url=f'https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/{REVISION}/raw/color/'+quote(CLASS[row['label']]+'/'+path.name)
            with urllib.request.urlopen(url,timeout=60) as response:raw=response.read()
            if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Download hash mismatch')
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(raw)
            downloaded+=1
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Existing file mismatch; retained without modification')
        verified+=1
    print(json.dumps({'source_revision':REVISION,'verified':verified,'downloaded':downloaded,'source_images_modified':False}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--verify-only',action='store_true')
    a=p.parse_args();reproduce(a.manifest,a.root,a.verify_only)
