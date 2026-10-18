"""Train a new small CNN on LinuxONE only. No pretrained weights or model downloads."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import time
from ml.audit import LABELS

def train(args):
    if platform.machine().lower()!='s390x':raise RuntimeError('Run training in the existing IBM LinuxONE container')
    provenance=json.loads(args.provenance.read_text())
    for key in ['source_url','license','license_url','verified_by','leaf_group_source']:
        if not isinstance(provenance.get(key),str) or not provenance[key].strip():raise ValueError('Verified provenance required: '+key)
    if provenance.get('verified') is not True:raise ValueError('Verify dataset provenance before training')
    rows=json.loads(args.manifest.read_text())
    if {r['label'] for r in rows}!=set(LABELS):raise ValueError('Exactly three tomato labels required')
    for key in ['group','pixel_sha256','sha256']:
        seen={}
        for r in rows:
            if r[key] in seen and seen[r[key]]!=r['split']:raise ValueError('Split leakage: '+key)
            seen[r[key]]=r['split']
    cutoff=datetime(2026,10,17,22,0,tzinfo=timezone.utc).timestamp() # 03:30 IST Oct 18
    if time.time()>=cutoff:raise RuntimeError('Feature/training freeze has passed; use existing artifacts')
    os.environ.setdefault('OMP_NUM_THREADS','3')
    os.environ.setdefault('TF_NUM_INTRAOP_THREADS','3')
    os.environ.setdefault('TF_NUM_INTEROP_THREADS','1')
    import numpy as np
    from PIL import Image, ImageOps
    import tensorflow as tf
    from sklearn.metrics import classification_report, confusion_matrix, balanced_accuracy_score
    tf.keras.utils.set_random_seed(2026)
    tf.config.threading.set_intra_op_parallelism_threads(3)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    args.out.mkdir(parents=True,exist_ok=False)
    start=time.time()
    arrays={}
    for split in ['train','val','test']:
        selected=[r for r in rows if r['split']==split]
        if set(r['label'] for r in selected)!=set(LABELS):raise ValueError('Each split needs all classes')
        images=[]
        for r in selected:
            path=(args.root/r['path']).resolve()
            if not path.is_relative_to(args.root.resolve()):raise ValueError('Path outside dataset')
            if hashlib.sha256(path.read_bytes()).hexdigest()!=r['sha256']:raise ValueError('Dataset changed since audit')
            with Image.open(path) as im:images.append(np.asarray(ImageOps.exif_transpose(im).convert('RGB').resize((96,96)),dtype=np.uint8))
        arrays[split]=(np.stack(images),np.array([LABELS.index(r['label']) for r in selected]))
    layers=tf.keras.layers
    model=tf.keras.Sequential([layers.Input((96,96,3)),layers.Rescaling(1/255),layers.RandomFlip('horizontal'),layers.RandomRotation(.08),
       layers.Conv2D(16,3,padding='same',activation='relu'),layers.MaxPool2D(),
       layers.Conv2D(32,3,padding='same',activation='relu'),layers.MaxPool2D(),
       layers.Conv2D(64,3,padding='same',activation='relu'),layers.GlobalAveragePooling2D(),
       layers.Dense(32,activation='relu'),layers.Dropout(.25),layers.Dense(3,activation='softmax')])
    model.compile(optimizer=tf.keras.optimizers.Adam(.001),loss='sparse_categorical_crossentropy',metrics=['accuracy'])
    class StopBudget(tf.keras.callbacks.Callback):
        def on_train_batch_end(self,batch,logs=None):
            if time.time()-start>=args.minutes*60 or time.time()>=cutoff:self.model.stop_training=True
    counts=Counter(arrays['train'][1].tolist());total=sum(counts.values())
    weights={k:total/(3*v) for k,v in counts.items()}
    options=tf.data.Options();options.threading.private_threadpool_size=3
    def dataset(split,shuffle=False):
        ds=tf.data.Dataset.from_tensor_slices(arrays[split])
        if shuffle:ds=ds.shuffle(len(arrays[split][0]),seed=2026)
        return ds.batch(32).with_options(options).prefetch(1)
    history=model.fit(dataset('train',True),validation_data=dataset('val'),epochs=args.epochs,class_weight=weights,
       callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss',patience=4,restore_best_weights=True),StopBudget()])
    # Test is evaluated once after training/validation decisions. No threshold tuning on test.
    scores=model.predict(dataset('test'),verbose=0);pred=scores.argmax(axis=1);truth=arrays['test'][1]
    metrics={'balanced_accuracy':float(balanced_accuracy_score(truth,pred)),
      'classification_report':classification_report(truth,pred,labels=[0,1,2],target_names=LABELS,output_dict=True,zero_division=0),
      'confusion_matrix':confusion_matrix(truth,pred,labels=[0,1,2]).tolist(),'test_images':len(truth),
      'limitation':'Internal controlled-background evaluation; not field accuracy. No external validation completed.'}
    model.save(args.out/'model.keras')
    info={'labels':LABELS,'input_size':96,'threshold':.75,'threshold_basis':'Fixed heuristic, not calibrated; no accuracy guarantee',
       'architecture':platform.machine(),'platform':platform.platform(),'python':platform.python_version(),'tensorflow':tf.__version__,
       'trained_at_utc':datetime.now(timezone.utc).isoformat(),'elapsed_seconds':time.time()-start,
       'epochs_completed':len(history.history['loss']),'trained_from_scratch':True,'seed':2026,
       'manifest_sha256':hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
       'model_sha256':hashlib.sha256((args.out/'model.keras').read_bytes()).hexdigest(),'provenance':provenance}
    for name,value in [('labels',dict(enumerate(LABELS))),('metadata',info),('metrics',metrics),('history',history.history)]:
        (args.out/(name+'.json')).write_text(json.dumps(value,indent=2))
    print(json.dumps(metrics,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True);p.add_argument('--provenance',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--epochs',type=int,default=20);p.add_argument('--minutes',type=int,default=30)
    train(p.parse_args())
