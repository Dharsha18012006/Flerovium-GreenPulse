"""Train an original CPU-efficient classifier, select on validation, evaluate test once."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import time
import joblib
import numpy as np
from PIL import Image, ImageOps
from sklearn.metrics import balanced_accuracy_score,classification_report,confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from ml.features import extract
from ml.audit import LABELS

def train(args):
    if platform.machine()!='s390x':raise ValueError('Train on LinuxONE')
    if datetime.now(timezone.utc)>=datetime(2026,10,17,22,0,tzinfo=timezone.utc):raise ValueError('Training freeze reached')
    rows=json.loads(args.manifest.read_text());provenance=json.loads(args.provenance.read_text())
    if provenance.get('verified') is not True:raise ValueError('Verified provenance required')
    if {r['split'] for r in rows}!={'train','val','test'}:raise ValueError('Invalid split')
    for key in ['group','pixel_sha256','sha256']:
        seen={}
        for r in rows:
            if r[key] in seen and seen[r[key]]!=r['split']:raise ValueError('Cross-split leakage: '+key)
            seen[r[key]]=r['split']
    for i,a in enumerate(rows):
        for b in rows[:i]:
            if a['split']!=b['split'] and (int(a['dhash'])^int(b['dhash'])).bit_count()<=4:
                raise ValueError('Cross-split near duplicate requires review')
    start=time.time();data={}
    for split in ['train','val','test']:
        subset=[r for r in rows if r['split']==split];x=[];y=[]
        if {r['label'] for r in subset}!=set(LABELS):raise ValueError('All classes required in every split')
        for row in subset:
            path=(args.root/row['path']).resolve()
            if not path.is_relative_to(args.root.resolve()):raise ValueError('Path outside project data')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Image changed since audit')
            with Image.open(path) as im:x.append(extract(ImageOps.exif_transpose(im)))
            y.append(LABELS.index(row['label']))
        data[split]=(np.stack(x),np.asarray(y))
    candidates=[];best=None;best_score=-1
    for c in [.1,1,10,100]:
        model=make_pipeline(StandardScaler(),SVC(C=c,kernel='rbf',gamma='scale',class_weight='balanced',probability=True,random_state=2026))
        model.fit(*data['train'])
        score=float(balanced_accuracy_score(data['val'][1],model.predict(data['val'][0])))
        candidates.append({'C':c,'validation_balanced_accuracy':score})
        print(candidates[-1],flush=True)
        if score>best_score:best_score=score;best=model
    args.out.mkdir(parents=True,exist_ok=False)
    # This is the sole final-test evaluation; selection above sees only validation.
    truth=data['test'][1];pred=best.predict(data['test'][0]);prob=best.predict_proba(data['test'][0])
    metrics={'balanced_accuracy':float(balanced_accuracy_score(truth,pred)),
       'classification_report':classification_report(truth,pred,labels=[0,1,2],target_names=LABELS,output_dict=True,zero_division=0),
       'confusion_matrix':confusion_matrix(truth,pred,labels=[0,1,2]).tolist(),'test_images':len(truth),
       'validation_candidates':candidates,'selected_validation_balanced_accuracy':best_score,
       'test_policy':'New supplemental physical leaf groups; excluded every known original leaf group. Selection uses validation only.',
       'limitation':'Small controlled-background holdout; not field accuracy or calibrated confidence. Original baseline test was used for development and is excluded here.'}
    joblib.dump(best,args.out/'model.joblib')
    info={'kind':'svm','labels':LABELS,'threshold':.75,'threshold_basis':'Fixed cautious heuristic; not a validated confidence threshold',
       'architecture':platform.machine(),'platform':platform.platform(),'python':platform.python_version(),
       'trained_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.time()-start,
       'trained_from_scratch':True,'pretrained_weights':False,'features':'Original 560-dimensional color, spatial moments, LBP and gradient descriptor',
       'manifest_sha256':hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
       'model_sha256':hashlib.sha256((args.out/'model.joblib').read_bytes()).hexdigest(),'provenance':provenance,
       'counts':{s:len(data[s][1]) for s in data},'selected_C':best.named_steps['svc'].C}
    for name,value in [('labels',dict(enumerate(LABELS))),('metadata',info),('metrics',metrics)]: (args.out/(name+'.json')).write_text(json.dumps(value,indent=2))
    print(json.dumps(metrics,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--provenance',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    train(p.parse_args())
