# Sources, licensing and dataset decision

Research and verification: October 17, 2026. Existing data audited before any image download. No original images, notebooks or unrelated files removed.

## Dataset comparison and decision

| Dataset | Published scope / license | Decision |
|---|---|---|
| PlantVillage | Author repository describes 54,306 images, 14 crops, 26 diseases. Author model card declares CC BY-SA 3.0. Controlled backgrounds; physical-leaf metadata available but incomplete. | Selected existing tomato classes plus bounded verified supplement. Fast CPU training; grouped evaluation and explicit field-domain limitation. |
| PlantDoc | Original repository describes 2,598 examples, 13 species and up to 17 disease types; CC BY 4.0. Internet-derived, more varied backgrounds, fewer examples per target class. | Not downloaded. Possible future external validation; not mixed into this hackathon training set. |

Primary sources:
- PlantVillage original repository: https://github.com/spMohanty/PlantVillage-Dataset
- Author dataset/license card: https://huggingface.co/datasets/mohanty/PlantVillage/blob/main/README.md
- Physical-leaf map pinned to verified source: https://raw.githubusercontent.com/spMohanty/PlantVillage-Dataset/7f7ecc7e1eaca78107e3affe7cb5abd9427e139a/leaf-map.json
- Mohanty, Hughes and Salathe (2016), Using Deep Learning for Image-Based Plant Disease Detection: https://doi.org/10.3389/fpls.2016.01419
- PlantDoc repository/license: https://github.com/pratikkayal/PlantDoc-Dataset
- Singh et al. (2020), PlantDoc: https://doi.org/10.1145/3371158.3371196

## Actual project data and splits

Original 375 images: 125 each healthy, early blight, late blight; existing 100 train/25 test per class. All decoded successfully; no exact pixel duplicates, split leakage or dHash distance<=4 candidates. Every file matches original RGB Git blob bytes at source commit 7f7ecc7e1eaca78107e3affe7cb5abd9427e139a. Reliable physical-leaf IDs cover 236: 125 early/60 late/51 healthy. Other 139 retained on disk, excluded from training.

Initial group split 164 train/36 validation/36 test supported a weak scratch CNN baseline. Its test was inspected, so those 36 images are quarantined from final training and final evaluation.

Supplemental 360 images (120/class) were fetched into a new folder. One image per unambiguous physical-leaf ID; all original filenames and all known original leaf IDs excluded. Availability checks rejected larger requested sets before downloading any images. Each download verified against upstream Git blob SHA1; all subsequently decoded, SHA256/pixel-hashed and grouped. Originals remain untouched.

Final combined manifest: 416 train, 90 validation, 54 test. Test consists solely of newly held-out supplemental leaf groups, 18/class. Original train/validation retained. Seeded 70/15/15 partitions at physical-leaf/duplicate connected-component level, seed 2026. Supplemental selection seed 2047. File hash, pixel hash, group-disjointness and dHash<=4 cross-split overlap checked before final training. Mapping and manifest checksums retained. No unsupported species added.

## Final preprocessing/model

EXIF orientation, RGB resize 96x96, original 560-dimensional RGB/HSV histograms/spatial means/std, local binary-pattern and gradient histograms. StandardScaler fitted to training only; RBF SVM trained from scratch. C in 0.1/1/10/100 compared using validation balanced accuracy only; C=10 chosen (first best). No pretrained model or encoder. Fixed 0.75 abstention heuristic is not a calibrated-confidence guarantee.

Actual final 54-image test: 51 correct (94.44%), balanced accuracy 94.44%, macro F1 0.9444. Validation balanced accuracy 89.61%. Model/evaluation on LinuxONE; see MODEL_CARD.md and evidence/. Controlled-background, small-sample results; no field validation, yield impact, outbreak detection or real-world accuracy claim.

Dataset files are not in Git or the source archive. Preserve PlantVillage attribution and CC BY-SA 3.0 terms when redistributing source images/adaptations. Demo leaf files, if exported, must include those notices. Never claim ownership of public dataset photographs.

## Care and nursery resources
- University of Maryland Extension, early blight: https://www.extension.umd.edu/resource/early-blight-tomatoes
- University of Maryland Extension, late blight: https://extension.umd.edu/resource/late-blight-tomato-and-potato
- University of Minnesota Extension, growing tomatoes: https://extension.umn.edu/vegetables/growing-tomatoes
- Original concise care paraphrases and Tamil translations; no copied source photographs; Tamil human review pending. General care only, no pesticide prescriptions.
- Official Google Maps URL API: https://developers.google.com/maps/documentation/urls/get-started . Encoded search query + api=1, no scraping or fabricated businesses. Typed-location handoff verified; browser geolocation permission flow not exercised.

## Software attribution
Installed libraries, not copied prior project code: FastAPI (MIT), Uvicorn (BSD-3-Clause), NumPy (BSD-3-Clause), Pillow (HPND), TensorFlow (Apache-2.0), scikit-learn (BSD-3-Clause), joblib (BSD-3-Clause), pytest (MIT), HTTPX (BSD-3-Clause). Python-multipart was initially listed but final raw-body image upload does not require it. Source projects:
https://github.com/fastapi/fastapi
https://github.com/encode/uvicorn
https://numpy.org
https://python-pillow.org
https://tensorflow.org
https://scikit-learn.org
https://joblib.readthedocs.io
https://pytest.org
https://www.python-httpx.org

Verified LinuxONE libraries: Python 3.12.15, TensorFlow 2.18.1, scikit-learn 1.9.0, Pillow 12.3.0, NumPy 2.0.2; isolated web env FastAPI 0.116.2 and Uvicorn 0.36.0. IBM-installed ML libraries preserved via venv path linkage.

Reproducibility update: download and verification scripts now pin the source revision already audited above. results/dataset-manifest.json preserves the exact custom leaf-separated partitions; they are not the official 80/20 split. ml/reproduce_dataset.py retrieves original bytes and checks each SHA256, preserving any existing file. Current s390x results are a verification repeat of the frozen model, not a new holdout claim. Training class imbalance is explicitly reported and handled with balanced class weights. No new data or weights were created in this continuation.

Application integration adds original frontend/deployment code and uses Python standard-library asyncio for the private socket proxy; no new external libraries, fonts, services or dataset downloads. Browser screenshots in results/web-desktop.png and web-mobile.png contain an attributed PlantVillage early-blight evaluation image; original source/license details above and artifacts/evidence/demo-leaves/ATTRIBUTION.md apply. Screenshots are execution evidence, not additional field-validation results.

Bilingual expansion source review (October 17, 2026): reopened all three Extension pages above and checked explanations/symptoms/prevention against their content. See CARE_REFERENCES.md for per-category mapping and regional limits. Original concise English/Tamil paraphrases, not official translations. No source images or text passages copied into the advice. Tamil human review remains pending. Runtime advice is curated, generated=false; no Granite or Gemini API integration.

Additional browser test image uncertain.jpg is an existing test leaf, not new data: PlantVillage source file b81b4276-e0c9-460a-ab94-79b6a5d0f2d6___RS_Erly.B 7538.JPG; SHA256 7c7ad3bc84706f3c347643ce8d671fe03ef1c243d20153b2afcb2f7b1f0e1f34. Same pinned source revision and CC BY-SA 3.0 attribution as the other demo leaves. Guidance screenshots are actual execution evidence, not additional field validation.

Community/marketplace continuation adds original application code only; no external datasets/services/packages added. Nursery discovery continues using the previously referenced official Google Maps search URL format, not scraped or fabricated business records. Five simulated test observations and two new clearly labeled demonstration form records were created solely for workflow verification; they are not evidence of real gardeners, sellers or plant disease.

Judging-readiness review adds no dataset, scientific claim, package or external AI service. Repeated frozen-model checks are not new independent evaluation. Rubric category names were supplied by the user; scores in READINESS_REPORT.md are the agent's evidence-based self-assessments, not official judge scores or a verification of organizer permission. Additional READINESS DEMO post/listing are test-only records.

## Release freeze
Release freeze adds no dataset, service, generated model or scientific claim. The final model/evidence bundle retains model metadata, metrics, frozen manifests, public demo image attribution and source references. Raw datasets/private runtime SQLite are excluded from the public repository and source archive. Existing controlled-background metrics remain repeat verification, not new independent evaluation.


Abstract audit October18: freshly checked the author PlantVillage raw README (https://huggingface.co/datasets/mohanty/PlantVillage/raw/main/README.md), which declares cc-by-sa-3.0 and physical-leaf grouping; checked official Google Maps URLs documentation (https://developers.google.com/maps/documentation/urls/get-started). URL construction is supported; actual business results remain unverified in this audit. No new dataset, library or care-content claim. See ABSTRACT_COMPLIANCE_AUDIT.md for limits of originality/license verification.


Nursery verification October18: actual Google Maps results for Chennai and Coimbatore, with Harith Tharang name/address corroborated at https://www.hariththarang.com/ and Tamara Garden Centre at https://www.tamaragardencentre.com/. Coordinates are Maps-reported only, not surveyed. Screenshots retain provider attribution; no scraped directory or copied photos integrated into product. See CONTACT_NURSERY_VERIFICATION.md. No business contacted. Reserved example.invalid appears only in explicitly marked contact tests, never as a real seller.
