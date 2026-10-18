# Classifier training, inference and evidence

Current model is already trained and tested on IBM LinuxONE. Do not tune further on the existing holdout. No old college weights were used. The selected artifact remains byte-identical to the original Datathon-trained SVM.

## What actually ran
The 96x96 scratch TensorFlow CNN ran on s390x for 20 epochs in 21.93 seconds, with early stopping and a 30-minute cap available. It was fast, but its initial 36-image development test was weak (44.44%). The final classifier is an original 560-feature RBF SVM, trained on LinuxONE in 4.30 seconds. The switch was motivated by the limited dataset and weak baseline, not by a fabricated CPU timeout. Its C value was selected using validation only; the inspected CNN test was excluded.

The original 375 images and all IBM notebooks remain intact. A balanced supplement of 120 independently identified leaves per class was added. Final combined training counts are 171 early blight, 119 healthy and 126 late blight; class weights compensate for that imbalance. Validation counts are 38/26/26; final test counts are 18/18/18. Thus the supplement/test are balanced, while the retained combined training data are not exactly balanced.

## Dataset reproduction
Source: original PlantVillage RGB repository, revision `7f7ecc7e1eaca78107e3affe7cb5abd9427e139a`, CC BY-SA 3.0 per author card. See SOURCES.md. The exact frozen manifest is `results/dataset-manifest.json`.

Within the existing notebook container, from `/home/ibm-user/shared/GreenPulseAI/release-20261017-2145`:
```sh
python -m ml.reproduce_dataset --manifest results/dataset-manifest.json --root /home/ibm-user/shared/GreenPulseAI --verify-only
```
To reproduce image bytes in a NEW directory, remove `--verify-only` and change `--root` to that new directory. The downloader uses pinned source URLs and SHA256 verification; matching files are retained and mismatches abort without overwriting. Original leaf grouping comes from the pinned author leaf-map. Custom group-separated partitions are used, not the official 80/20 benchmark split; do not claim benchmark comparability. Original train/validation and supplemental partitions are recorded explicitly. No overlapping physical leaf groups, exact hashes or close dHash matches cross final splits.

## Training commands (only if an intentional reproduction is needed before freeze)
These create new artifacts; do not point output at the selected model directory. Existing IBM packages suffice; no heavy install needed. Source scripts refuse new training after the event's 03:30 IST cutoff.
```sh
python -m ml.train --root /home/ibm-user/shared/GreenPulseAI/data/raw --manifest artifacts/split-01/split.json --provenance artifacts/verified-01/provenance.json --out artifacts/cnn-reproduction --epochs 20 --minutes 30

python -m ml.train_svm --root /home/ibm-user/shared/GreenPulseAI --manifest results/dataset-manifest.json --provenance artifacts/verified-02/provenance.json --out artifacts/svm-reproduction
```
The first command reproduces the original CNN baseline, not a head-to-head comparison with the larger final SVM dataset. To train the CNN on the final frozen dataset, use the second command's root/manifest/provenance with `ml.train`; no such additional training was done for this milestone.

## Inference and verification
```sh
.venv/bin/python -m ml.inference --model-dir artifacts/model-svm --image artifacts/demo-leaves/early_blight.jpg

.venv/bin/python -m scripts.evaluate_saved --root /home/ibm-user/shared/GreenPulseAI --manifest results/dataset-manifest.json --model-dir artifacts/model-svm --out results/new-verification

.venv/bin/python -m pytest -q
```
Inference accepts uploaded image bytes through `LeafClassifier.predict_bytes`. It returns class, confidence/score, uncertainty and limitations; it never imports or generates care guidance. The existing API composes separately sourced care into its presentation response. Model loading/inference requires s390x and verifies artifact integrity and label order.

Supported inputs: nonempty, valid single-frame JPEG or PNG, maximum 5 MB / 16 megapixels, minimum 32 pixels per side. Unsupported/damaged/animated images return a clear validation error. WebP is deliberately excluded because the existing LinuxONE Pillow build lacks its codec. Other plant species and unseen diseases cannot be reliably recognized as unsupported; even high scores can be wrong. Scores are not validated confidence estimates. Below 0.75, the result is explicitly uncertain and the app withholds disease-specific care.

The current `results/classifier-verification-01/` records a recheck of the frozen model on its existing test set, not a new independent evaluation. Accuracy 51/54 (94.44%), macro F1 0.94436. Warm median 7.02 ms, p95 7.31 ms across 53 calls; first call 62.49 ms includes model loading with Python libraries already imported. Latency includes decode/features/classification but excludes network/HTTP. Small controlled-background results do not establish field diagnostic accuracy.

Model artifact: remote `artifacts/model-svm/model.joblib`; local backup `artifacts/evidence/model-svm/model.joblib`. Load only this trusted project artifact. Explicit label mapping and CSV/PNG confusion matrices are in results. A live private app remains at localhost:8003 via the existing SSH tunnel (DEPLOYMENT.md).
