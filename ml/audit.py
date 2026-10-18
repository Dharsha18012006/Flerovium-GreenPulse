"""Read-only image audit. Writes only a new output directory, never touches source images."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import platform
import warnings
from PIL import Image, ImageOps

LABELS = ['early_blight','healthy','late_blight']
ALIASES = {'tomatoearlyblight':'early_blight','tomatohealthy':'healthy','tomatolateblight':'late_blight'}

def classify(path):
    for part in reversed(path.parts[:-1]):
        key = ''.join(c for c in part.lower() if c.isalnum())
        if key in ALIASES:
            return ALIASES[key]
    return None

def fingerprint(path):
    with warnings.catch_warnings():
        warnings.simplefilter('error',Image.DecompressionBombWarning)
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            im = ImageOps.exif_transpose(im).convert('RGB')
            im.load()
            if im.width*im.height>16_000_000:
                raise ValueError('over 16 megapixels')
            pixel = hashlib.sha256(str(im.size).encode()+im.tobytes()).hexdigest()
            # Difference hash flags possible near duplicates; not proof of leaf identity.
            small = im.convert('L').resize((9,8))
            tiny = list(small.get_flattened_data() if hasattr(small,'get_flattened_data') else small.getdata())
            bits = [tiny[y*9+x]>tiny[y*9+x+1] for y in range(8) for x in range(8)]
            dhash = sum(int(b)<<i for i,b in enumerate(bits))
            return im.size,pixel,dhash

def audit(root, out):
    root = root.resolve()
    if not root.is_dir():
        raise ValueError('Dataset directory does not exist')
    out.mkdir(parents=True,exist_ok=False)
    records, errors, unknown = [], [], Counter()
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in {'.jpg','.jpeg','.png','.webp','.bmp'}:
            continue
        if not path.resolve().is_relative_to(root):
            continue
        label = classify(path.relative_to(root))
        if label is None:
            unknown[path.parent.name] += 1
            continue
        rel = path.relative_to(root).as_posix()
        try:
            size,pixel,dhash = fingerprint(path)
            parts = {s.lower() for s in path.relative_to(root).parts[:-1]}
            split = next((s for s in ['test','val','valid','validation','train'] if s in parts),'unspecified')
            records.append({'path':rel,'label':label,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                            'pixel_sha256':pixel,'dhash':str(dhash),'width':size[0],'height':size[1],'existing_split':split})
        except Exception as exc:
            errors.append({'path':rel,'error':type(exc).__name__})
    by_hash = defaultdict(list)
    for row in records:
        by_hash[row['pixel_sha256']].append(row)
    duplicates = [[r['path'] for r in group] for group in by_hash.values() if len(group)>1]
    leakage = [group for group in by_hash.values() if len({r['existing_split'] for r in group})>1]
    conflicts = [group for group in by_hash.values() if len({r['label'] for r in group})>1]
    # Pairwise scan is bounded for the intended small three-class audit.
    near_pairs = []
    unique = [g[0] for g in by_hash.values()]
    near_scan_complete = len(unique)<=10000
    if near_scan_complete:
        for i,a in enumerate(unique):
            ha = int(a['dhash'])
            for b in unique[:i]:
                if (ha^int(b['dhash'])).bit_count()<=4:
                    near_pairs.append([a['path'],b['path']])
    summary = {'root':str(root),'architecture':platform.machine(),'valid_images':len(records),
               'class_counts':dict(Counter(r['label'] for r in records)),
               'existing_split_counts':dict(Counter(r['existing_split']+':'+r['label'] for r in records)),
               'corrupt_images':errors,'unrecognized_class_counts':dict(unknown),
               'exact_duplicate_groups':duplicates,'duplicate_split_leaks':leakage,
               'conflicting_labels':conflicts,'near_duplicate_candidates':near_pairs,
               'near_scan_complete':near_scan_complete,
               'note':'No source images altered. Near matches need review. Leaf metadata and provenance must be verified before training.'}
    (out/'manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    (out/'audit.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k in ['architecture','valid_images','class_counts','existing_split_counts','near_scan_complete']},indent=2))
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();audit(a.root,a.out)
