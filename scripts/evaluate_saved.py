"""Verify the frozen classifier on LinuxONE; does not fit or select a model."""
import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time
import numpy as np
import sklearn
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from ml.inference import LeafClassifier

def evaluate(root, manifest, model_dir, out):
    if platform.machine() != 's390x':
        raise RuntimeError('Execution evidence must be collected on LinuxONE s390x.')
    rows=json.loads(manifest.read_text())
    metadata=json.loads((model_dir/'metadata.json').read_text())
    labels=metadata['labels'];classifier=LeafClassifier(model_dir)
    predictions=[];times=[];truth=[];pred=[]
    for row in rows:
        if row['split']!='test':continue
        path=(root/row['path']).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('Path outside dataset')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('Test image changed')
        start=time.perf_counter();result=classifier.predict_bytes(raw);elapsed=time.perf_counter()-start
        truth.append(row['label']);pred.append(result['label']);times.append(elapsed)
        predictions.append({'expected':row['label'],'sha256':row['sha256'],'elapsed_seconds':elapsed,**result})
    if not truth:raise ValueError('No held-out test images')
    out.mkdir(parents=True,exist_ok=False)
    matrix=confusion_matrix(truth,pred,labels=labels).tolist()
    metrics={'accuracy':float(accuracy_score(truth,pred)),
             'macro_f1':float(f1_score(truth,pred,labels=labels,average='macro',zero_division=0)),
             'confusion_matrix':matrix,'labels':labels,'test_images':len(truth),
             'per_class':classification_report(truth,pred,labels=labels,output_dict=True,zero_division=0),
             'split_class_counts':{split:dict(Counter(r['label'] for r in rows if r['split']==split)) for split in ['train','val','test']},
             'methodology':'Verification of frozen model on its existing final holdout; no retraining, tuning, or new independent evaluation.',
             'limitations':'Small controlled-background PlantVillage test. Unsupported species/diseases are not reliably detected; confidence scores are not calibrated.'}
    warm=np.asarray(times[1:])
    latency={'cold_request_seconds':times[0],'warm_requests':len(warm),
             'warm_median_seconds':float(np.median(warm)), 'warm_p95_seconds':float(np.percentile(warm,95)),
             'scope':'Sequential predict_bytes including decoding and features; first request includes model loading. Excludes SSH/network and HTTP.'}
    execution={'architecture':platform.machine(),'platform':platform.platform(),'python':platform.python_version(),'scikit_learn':sklearn.__version__,
               'verified_at_utc':datetime.now(timezone.utc).isoformat(),'model_sha256':metadata['model_sha256'],
               'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'training_metadata':metadata}
    for name,value in [('metrics',metrics),('latency',latency),('execution',execution),('predictions',predictions),('labels',dict(enumerate(labels)))]:
        (out/(name+'.json')).write_text(json.dumps(value,indent=2),encoding='utf-8')
    with (out/'confusion_matrix.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['true / predicted',*labels])
        writer.writerows([[label,*values] for label,values in zip(labels,matrix)])
    print(json.dumps({'metrics':metrics,'latency':latency},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--model-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();evaluate(a.root,a.manifest,a.model_dir,a.out)
