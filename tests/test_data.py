import json
import random
from pathlib import Path
import pytest
from PIL import Image
from ml.audit import audit, LABELS
from ml.split import make_split

def test_audit_detects_corruption_duplicates_and_leakage(tmp_path):
    root=tmp_path/'raw'
    for split in ['train','test']:
        folder=root/split/'Tomato___Early_blight';folder.mkdir(parents=True)
        Image.new('RGB',(20,20),'green').save(folder/'same.png')
    (root/'train/Tomato___Early_blight/broken.jpg').write_bytes(b'not an image')
    report=audit(root,tmp_path/'audit')
    assert report['valid_images']==2
    assert len(report['corrupt_images'])==1
    assert len(report['duplicate_split_leaks'])==1
    assert len(list(root.rglob('*.png')))==2

def test_split_requires_groups_and_keeps_related_images_together(tmp_path):
    folder=tmp_path/'audit';folder.mkdir()
    rows=[];groups={}
    for label in LABELS:
        for i in range(30):
            path=f'{label}/{i}.png'
            rows.append({'path':path,'label':label,'pixel_sha256':path,'sha256':path})
            groups[path]=f'{label}-leaf-{i//2}'
    # 15 independent groups should fail rather than creating tiny evaluation sets.
    (folder/'manifest.json').write_text(json.dumps(rows))
    (folder/'audit.json').write_text(json.dumps({'conflicting_labels':[],'near_scan_complete':True,'near_duplicate_candidates':[]}))
    gp=tmp_path/'groups.json';gp.write_text('{}')
    with pytest.raises(ValueError,match='Every audited'):make_split(folder,gp,tmp_path/'bad')
    gp.write_text(json.dumps(groups))
    with pytest.raises(ValueError,match='at least 20'):make_split(folder,gp,tmp_path/'small')
    for row in rows:groups[row['path']]=row['path']
    gp.write_text(json.dumps(groups))
    report=json.loads((folder/'audit.json').read_text());report['near_duplicate_candidates']=[['healthy/0.png','healthy/1.png']]
    (folder/'audit.json').write_text(json.dumps(report))
    make_split(folder,gp,tmp_path/'valid')
    result=json.loads((tmp_path/'valid/split.json').read_text())
    lookup={r['path']:r for r in result}
    assert lookup['healthy/0.png']['split']==lookup['healthy/1.png']['split']
    memberships={}
    for r in result:memberships.setdefault(r['group'],set()).add(r['split'])
    assert all(len(s)==1 for s in memberships.values())
    assert {r['split'] for r in result}=={'train','val','test'}
