from io import BytesIO
import pytest
from PIL import Image
from ml.inference import decode_image, InvalidImage, LeafClassifier, ModelUnavailable, format_prediction
from ml.audit import LABELS

def photo(fmt='PNG', size=(64,64)):
    data=BytesIO();Image.new('RGB',size,'green').save(data,format=fmt);return data.getvalue()

@pytest.mark.parametrize('raw',[b'',b'not an image',photo('GIF'),photo(size=(8,8)),photo()[:30]])
def test_invalid_inputs_rejected(raw):
    with pytest.raises(InvalidImage):decode_image(raw)

def test_supported_formats_and_grayscale():
    for fmt in ['JPEG','PNG']:
        assert decode_image(photo(fmt)).size==(96,96)
    data=BytesIO();Image.new('L',(64,64),100).save(data,format='PNG')
    assert decode_image(data.getvalue()).mode=='RGB'

def test_animated_png_is_rejected():
    data=BytesIO()
    Image.new('RGB',(64,64),'green').save(data,format='PNG',save_all=True,append_images=[Image.new('RGB',(64,64),'red')],duration=100)
    with pytest.raises(InvalidImage,match='animation'):decode_image(data.getvalue())

def test_uncertainty_is_explicit_and_no_care_is_generated():
    # Synthetic unit-test scores only; never used as evaluation or app predictions.
    result=format_prediction(LABELS,[.4,.3,.3],0,.75)
    assert result['uncertain'] and result['confidence']==.4
    assert 'guidance' not in result

def test_missing_artifact_is_controlled_error(tmp_path,monkeypatch):
    monkeypatch.setattr('ml.inference.platform.machine',lambda:'s390x')
    with pytest.raises(ModelUnavailable,match='could not be loaded'):
        LeafClassifier(tmp_path).predict_bytes(photo())
