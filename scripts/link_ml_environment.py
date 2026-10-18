"""Run with original notebook Python to link its existing ML libs into project venv."""
from pathlib import Path
import site
import sys

root=Path(__file__).resolve().parent.parent
target=root/'.venv/lib/python3.12/site-packages/ibm_ml.pth'
paths=[p for p in site.getsitepackages() if p.startswith('/opt/venv/')]
if not paths or not target.parent.is_dir():raise RuntimeError('Unexpected notebook or project environment')
with target.open('x') as f:f.write('\n'.join(paths)+'\n')
print('Linked existing IBM ML site-packages into the isolated project environment.')
