"""LinuxONE image classification only: no care text, network calls or image persistence."""
from io import BytesIO
from pathlib import Path
import argparse
import hashlib
import json
import platform
import threading
import warnings
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from ml.audit import LABELS

MAX_BYTES = 5 * 1024 * 1024

class InvalidImage(ValueError):
    pass

class ModelUnavailable(RuntimeError):
    pass

def decode_image(raw):
    if not raw:
        raise InvalidImage('The uploaded image is empty.')
    if len(raw) > MAX_BYTES:
        raise InvalidImage('Use an image no larger than 5 MB.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format not in ('JPEG', 'PNG'):
                    raise InvalidImage('Unsupported format. Use JPEG or PNG.')
                if getattr(image, 'n_frames', 1) != 1:
                    raise InvalidImage('Use a single still image, not an animation.')
                if image.width * image.height > 16_000_000 or min(image.size) < 32:
                    raise InvalidImage('Use a photo at least 32 pixels on each side, up to 16 megapixels.')
                return ImageOps.exif_transpose(image).convert('RGB').resize((96, 96))
    except InvalidImage:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise InvalidImage('Invalid or damaged image. Use JPEG or PNG.') from exc

def format_prediction(labels, scores, index, threshold):
    scores = np.asarray(scores, dtype=float)
    if scores.shape != (3,) or not np.isfinite(scores).all() or np.any(scores < 0) or np.any(scores > 1):
        raise ModelUnavailable('Model returned invalid scores.')
    confidence = float(scores[index])
    uncertain = confidence < threshold
    return {'label': labels[index], 'score': confidence, 'confidence': confidence,
            'uncertain': uncertain,
            'message': 'Uncertain: retake a clear single tomato-leaf photo or ask an expert.' if uncertain else 'Experimental pattern match, not a confirmed diagnosis.',
            'limitations': 'Tomato only; three classes. Other plants and diseases may still receive a high score. Scores are not calibrated probabilities.',
            'architecture': platform.machine(), 'image_stored': False}

class LeafClassifier:
    def __init__(self, model_dir):
        self.model_dir = Path(model_dir)
        self.model = None
        self.metadata = None
        self.lock = threading.Lock()

    def _load(self):
        if platform.machine().lower() != 's390x':
            raise ModelUnavailable('Project inference is enabled only on IBM LinuxONE (s390x).')
        if self.model is not None:
            return
        try:
            meta = json.loads((self.model_dir / 'metadata.json').read_text())
            if meta.get('architecture') != 's390x' or meta.get('trained_from_scratch') is not True or meta.get('labels') != LABELS:
                raise ModelUnavailable('Model provenance or label mapping is invalid.')
            filename = 'model.joblib' if meta.get('kind') == 'svm' else 'model.keras'
            path = self.model_dir / filename
            if hashlib.sha256(path.read_bytes()).hexdigest() != meta['model_sha256']:
                raise ModelUnavailable('Model integrity check failed.')
            if meta.get('kind') == 'svm':
                import joblib
                # Trusted, project-generated artifact only; never accept uploaded models.
                model = joblib.load(path)
            else:
                import tensorflow as tf
                tf.config.threading.set_intra_op_parallelism_threads(3)
                tf.config.threading.set_inter_op_parallelism_threads(1)
                model = tf.keras.models.load_model(path, compile=False)
            self.metadata, self.model = meta, model
        except ModelUnavailable:
            raise
        except Exception as exc:
            raise ModelUnavailable('Model could not be loaded; check its files and runtime dependencies.') from exc

    def predict_bytes(self, raw):
        image = decode_image(raw)
        with self.lock:
            self._load()
            if self.metadata.get('kind') == 'svm':
                from ml.features import extract
                features = extract(image)[None, ...]
                scores = self.model.predict_proba(features)[0]
                index = int(self.model.predict(features)[0])
            else:
                scores = self.model(np.asarray(image, dtype=np.float32)[None, ...], training=False).numpy()[0]
                index = int(np.argmax(scores))
            return format_prediction(self.metadata['labels'], scores, index, self.metadata.get('threshold', .75))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-dir', type=Path, required=True)
    parser.add_argument('--image', type=Path, required=True)
    args = parser.parse_args()
    with args.image.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    print(json.dumps(LeafClassifier(args.model_dir).predict_bytes(raw), indent=2))
