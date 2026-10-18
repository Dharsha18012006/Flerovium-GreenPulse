"""Print only allowlisted environment facts, never environment variables or credentials."""
import importlib.metadata
import json
import os
import platform
import shutil

facts={'architecture':platform.machine(),'os':platform.system(),'python':platform.python_version(),'cpus':os.cpu_count(),
       'disk_free_bytes':shutil.disk_usage('.').free,'packages':{}}
for package in ['fastapi','uvicorn','python-multipart','Pillow','numpy','tensorflow','scikit-learn']:
    try:facts['packages'][package]=importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:facts['packages'][package]='missing'
print(json.dumps(facts,indent=2))
