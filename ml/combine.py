"""Retain original train/validation, quarantine inspected baseline test, add new groups."""
import argparse
import json
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--supplement',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();base=json.loads(a.base.read_text());extra=json.loads(a.supplement.read_text())
    result=[]
    for row in base:
        if row['split']=='test':continue
        result.append({**row,'path':'data/raw/'+row['path']})
    for row in extra:result.append({**row,'path':'release-20261017-2145/artifacts/supplement-01/'+row['path']})
    with a.out.open('x') as f:json.dump(result,f,indent=2)
    print('Combined original train/validation and new grouped supplement; inspected baseline test excluded.')
