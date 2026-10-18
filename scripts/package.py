"""Create a source-only archive; no datasets, credentials, models or runtime state."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import tarfile

root=Path(__file__).resolve().parent.parent
allowed={'app','ml','scripts','tests','evidence','results'}
files=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
dest=root/'releases';dest.mkdir(exist_ok=True)
output=dest/('greenpulse-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.tar.gz')
with tarfile.open(output,'x:gz') as archive:
    for name in files:
        p=Path(name)
        if not name:continue
        if p.parts[0] in allowed or (len(p.parts)==1 and (p.suffix=='.md' or name in ['requirements.txt','requirements-dev.txt','requirements-ml.txt','.gitignore','.gitattributes'])):
            full=root/p
            if full.is_symlink() or not full.resolve().is_relative_to(root):raise ValueError('Unsafe source path')
            if full.suffix.lower() in {'.py','.js','.css','.html','.md','.txt','.json','.csv','.png','.sh'} or name in ['.gitignore','.gitattributes']:archive.add(full,arcname=name)
print(output)
