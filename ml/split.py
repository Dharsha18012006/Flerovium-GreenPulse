"""Create deterministic group-disjoint partitions from an audited manifest.

Requires a manually verified JSON mapping of relative image paths to physical leaf IDs.
Near-duplicate candidates are unioned conservatively. Nothing is downloaded or deleted.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
from ml.audit import LABELS

def make_split(audit_dir, groups_path, out):
    rows=json.loads((audit_dir/'manifest.json').read_text())
    report=json.loads((audit_dir/'audit.json').read_text())
    groups=json.loads(groups_path.read_text())
    if report['conflicting_labels'] or not report['near_scan_complete']:
        raise ValueError('Resolve conflicting labels or incomplete near-duplicate audit first')
    if not rows or any(not isinstance(groups.get(r['path']),str) or not groups[r['path']].strip() for r in rows):
        raise ValueError('Every audited image needs a verified physical leaf ID')
    parent={r['path']:r['path'] for r in rows}
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):
        parent[find(a)]=find(b)
    buckets=defaultdict(list)
    for r in rows:
        buckets['leaf:'+groups[r['path']]].append(r['path'])
        buckets['hash:'+r['pixel_sha256']].append(r['path'])
    for bucket in buckets.values():
        for path in bucket[1:]:union(bucket[0],path)
    for a,b in report['near_duplicate_candidates']:union(a,b)
    components=defaultdict(list)
    seen=set()
    for r in rows:
        if r['pixel_sha256'] in seen:continue
        seen.add(r['pixel_sha256'])
        components[find(r['path'])].append(r)
    by_class=defaultdict(list)
    for items in components.values():
        labels={r['label'] for r in items}
        if len(labels)!=1:raise ValueError('Near-duplicate or leaf group crosses labels; review before splitting')
        by_class[items[0]['label']].append(items)
    result=[]
    rng=random.Random(2026)
    for label in LABELS:
        items=by_class[label];rng.shuffle(items)
        if len(items)<20:raise ValueError(f'{label} needs at least 20 independent leaf groups')
        # Whole groups split 70/15/15; image counts may vary with group sizes.
        n=len(items);ntrain=int(n*.7);nval=int(n*.15)
        for i,group in enumerate(items):
            partition='train' if i<ntrain else 'val' if i<ntrain+nval else 'test'
            gid=hashlib.sha256('|'.join(sorted(r['path'] for r in group)).encode()).hexdigest()
            for r in group:result.append({**r,'group':gid,'split':partition})
    out.mkdir(parents=True,exist_ok=False)
    (out/'split.json').write_text(json.dumps(result,indent=2))
    (out/'split_summary.json').write_text(json.dumps({'seed':2026,'method':'physical leaf IDs + exact pixels + conservative dHash<=4 components; deduplicate; 70/15/15 groups within class',
      'counts':dict(Counter(r['split']+':'+r['label'] for r in result)),
      'groups_mapping_sha256':hashlib.sha256(groups_path.read_bytes()).hexdigest(),
      'existing_partitions':'Replaced only in new manifest; original files and splits untouched.'},indent=2))
    print('Saved group-disjoint manifest:',out/'split.json')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--groups',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();make_split(a.audit,a.groups,a.out)
