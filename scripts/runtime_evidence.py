"""Selective LinuxONE provenance evidence; never reads secrets or environment variables."""
import hashlib
import json
from pathlib import Path
import platform
from PIL import Image
from ml.inference import LeafClassifier
from ml.features import extract

root=Path(__file__).resolve().parent.parent
classifier=LeafClassifier(root/'artifacts/model-svm')
classifier._load()
model=classifier.model
width=len(extract(Image.new('RGB',(96,96),'green')))
assert width==model.n_features_in_==560
assert list(map(int,model.classes_))==[0,1,2]
files=['app/main.py','app/care.py','app/static/index.html','app/static/app.js','app/static/guidance.js','app/static/style.css','ml/inference.py','ml/features.py','ml/audit.py','scripts/private_proxy.py','scripts/start_private.sh']
result={'architecture':platform.machine(),'python':platform.python_version(),'model_kind':classifier.metadata['kind'],'model_sha256':classifier.metadata['model_sha256'],'labels':classifier.metadata['labels'],'estimator_classes':list(map(int,model.classes_)),'feature_width':width,'preprocessing':'EXIF transpose, RGB, 96x96; fixed image features and fitted scaler in final SVM pipeline','contract_check':'Synthetic solid image used only to check feature dimensionality; no synthetic prediction or metric claimed. Actual held-out inference is in readiness-model-01 and readiness-http.json.','source_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in files},'acceleration':'No NNPA or zDNN runtime evidence collected; no acceleration claim.'}
print(json.dumps(result,indent=2))
