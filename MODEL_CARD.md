# GreenPulse tomato classifier — frozen model

Trained from scratch on IBM LinuxONE s390x on October 17, 2026. No pretrained weights or prior college-project assets used.

Model: StandardScaler + RBF support-vector classifier (C=10, gamma=scale, balanced class weights). Original 560-dimensional descriptor: RGB/HSV histograms, spatial moments, local binary patterns and gradient orientation. The descriptor has no pretrained encoder. Four C values selected using validation balanced accuracy; test evaluated after selection.

Data: original PlantVillage RGB images, CC BY-SA 3.0, author repository commit 7f7ecc7e1eaca78107e3affe7cb5abd9427e139a. All images byte-verified against Git blob hashes. Existing 375 images preserved. 236 had unambiguous physical leaf IDs; baseline test 36 is quarantined from final training/evaluation. Added 360 images (120/class), one per physical leaf, excluding all known original groups. Missing/ambiguous original metadata images were not used. Final train 416, validation 90, test 54. Test contains only newly held-out groups, 18/class. Exact pixel and close dHash overlap checks enforced across final splits.

## Actual results

| Metric | Value |
|---|---:|
| Validation balanced accuracy | 89.61% |
| Final test accuracy | 94.44% (51/54) |
| Final test balanced accuracy | 94.44% |
| Final test macro F1 | 0.9444 |
| Training/feature extraction/selection elapsed | 4.30 seconds |

Confusion matrix (rows true; columns predicted; order early blight, healthy, late blight):
```
18  0  0
 0 17  1
 2  0 16
```
Model SHA256: e8b84cbdd83a6647b9f2538a39f5d73d3dbd0213293912283f11b42259bd995c.

## Limits
Only three tomato categories; unsupported plants/diseases can produce high scores. Controlled backgrounds can create shortcut learning. Small holdout, no independent field validation, no impact measurement. 94.44% is not real-world diagnostic accuracy. Threshold 0.75 is a fixed heuristic; returned scores are not validated confidence estimates. Tamil translations await human review. Do not choose pesticide treatment from this output alone.

The initial scratch CNN achieved 44.44% on a different 36-image development holdout. This motivated the revised approach; that test was not reused as the final benchmark. These figures are not a head-to-head comparison because the datasets differ. Final classifier is now frozen, with no test-driven retuning.

Actual serving evidence: first test image per class through the LinuxONE HTTP API, all 3 matched expected labels; cold request 0.550s and subsequent requests 0.0089s/0.0077s inside VM. These three timings are smoke-test measurements, not a latency benchmark. See evidence/ JSON files.
