# Flerovium — Urban Green Connect AI: GreenPulse

IBM Z Datathon2026 · Wildcard: Beyond the Obvious

GreenPulse is a private, functional gardening prototype: new tomato-leaf classification, curated English/Tamil guidance, community posts, a small marketplace with explicitly consented seller email, external Google Maps nursery discovery, and coarse-area voluntary observation summaries.

## Verified scope

Actual model training and inference ran on IBM LinuxONE s390x. The final model is a newly trained560-feature RBF SVM, not an IBM tutorial model, prior project model or runtime LLM. On54 leaf-separated PlantVillage test images it achieved51correct predictions (94.44%accuracy, macroF1 .9444). Only healthy tomato leaves, early blight and late blight are supported. Controlled-background evaluation does not establish real-world diagnostic accuracy. Scores are uncalibrated; unknown species may receive high scores.

Final verification:27tests passed on LinuxONE and Windows;26live API smoke checks passed, including8real predictions across EN/TA and uncertainty. See results/final-submission-smoke.json and final-submission-linuxone-tests.txt. Labeled DEMO posts/listings and simulated health reports are not real transactions or outbreaks. No payments, expert verification, authentication or production public service is claimed.

## Repository layout

`app/`: FastAPI, care content, HTML/CSS/JavaScript. `ml/`: dataset reproduction, grouping, training and inference. `scripts/`: startup, private proxy, verification. `tests/`: regression tests. `results/`: dataset manifest and selected actual evidence. `SOURCES.md` and `CARE_REFERENCES.md`: attribution. `MODEL_CARD.md`: scientific limitations.

No credentials, private database, raw dataset or virtual environment is included. The original private Git history remains preserved separately; this ZIP is a publication-ready source snapshot, not a history rewrite. The team must approve actual publication. Project-specific source has no newly assigned public license; do not infer that third-party licenses automatically license the team's own code.

## Existing LinuxONE demonstration

The verified existing host release is `/home/linux1/shared/GreenPulseAI/release-20261017-2145`, mounted in container `notebook` at `/home/ibm-user/shared/GreenPulseAI/release-20261017-2145`. Installed project `.venv` links the existing IBM ML environment. Use the existing deployment; do not recreate its VM/container or expose notebook/API ports.

```bash
# Existing LinuxONE host shell: check before starting anything
curl --max-time 10 http://127.0.0.1:8003/api/health
sudo -n docker exec -w /home/ibm-user/shared/GreenPulseAI/release-20261017-2145 notebook .venv/bin/python -m pytest -q
sudo -n docker exec -w /home/ibm-user/shared/GreenPulseAI/release-20261017-2145 notebook .venv/bin/python -m scripts.runtime_evidence
```

If stopped, run `bash scripts/start_private.sh` from the host release. It uses a shared Unix socket and a host-loopback proxy; it refuses to replace an existing socket. If only the proxy stopped, run `python3 scripts/private_proxy.py --socket "$PWD/run/greenpulse.sock" --port 8003`. Never blindly remove a live socket.

From your local machine, substitute your own existing identity path and server hostname (never put key contents in commands, Git or screenshots):

```bash
ssh -i /path/to/existing-key -o ExitOnForwardFailure=yes -o ServerAliveInterval=15 -N -L 127.0.0.1:8003:127.0.0.1:8003 linux1@YOUR_EXISTING_LINUXONE_HOST
```

Open http://127.0.0.1:8003. A localhost URL is not a public demo link for judges; the submitted video demonstrates the private app.

## Model and data reproduction

The separately prepared `Flerovium_GreenPulse_Model.zip` contains the newly trained model, labels and metadata under `artifacts/model-svm/`. Check its manifest; load only trusted project artifacts. It does not include raw photographs. Existing server artifacts remain unchanged. Inference requires s390x and checks metadata and the model SHA256.

```bash
# Inside the existing notebook container release
.venv/bin/python -m ml.reproduce_dataset --manifest results/dataset-manifest.json --root /home/ibm-user/shared/GreenPulseAI --verify-only
.venv/bin/python -m scripts.evaluate_saved --root /home/ibm-user/shared/GreenPulseAI --manifest results/dataset-manifest.json --model-dir artifacts/model-svm --out results/new-evaluation
```

For exact image reconstruction in a NEW destination, remove `--verify-only` and use that new root; existing mismatched files are never overwritten. Preserve PlantVillageCC BY-SA3.0 attribution. No dataset download is needed for the existing demo.

Training scripts and CLASSIFIER_RUNBOOK.md preserve the original method. Training deliberately stops after the fixed03:30ISTcode freeze; post-event retraining requires an explicitly reviewed change to that guard. Saved-model evaluation remains reproducible without retraining. Do not tune against the published test set.

## Dependencies and privacy

Verified environment: Python3.12.15, scikit-learn1.9.0, NumPy2.0.2, Pillow12.3.0, FastAPI0.116.2, Uvicorn0.36.0; TensorFlow2.18.1 was used for the earlier CNN experiment. Requirement files describe dependency bounds; this is not a claim of compatibility with every future version or other architecture. Do not perform heavy upgrades before demonstration.

Photos are processed in memory. Community information is user-generated; seller email is public only after explicit consent. Reports use coarse areas and minimum-five summaries over seven days; duplicates can inflate counts. Nursery search transfers the query to Google Maps externally. This private prototype requires further abuse controls, authentication, field validation and review before public deployment.

## Originality and credits

Project-specific code and selected weights were created during the Datathon; no prior college source/model was reused in this work. AI coding assistance was used; organizer clarification remains pending, not assumed approved or prohibited. Data/library/care credits are in SOURCES.md. No measured yield, adoption or treatment-impact claims are made.
