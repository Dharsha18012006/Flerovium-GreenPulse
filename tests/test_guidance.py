"""Guidance contract and prediction separation, with synthetic unit data only."""
import pytest
from app.care import get_guidance
from app import main

@pytest.mark.parametrize('label',['healthy','early_blight','late_blight'])
@pytest.mark.parametrize('language',['en','ta'])
def test_guidance_contract(label,language):
    value=get_guidance(label,language)
    assert value['language']==language and value['generated'] is False
    assert value['content_type']=='curated'
    for key in ['explanation','symptoms','prevention','steps','scope','notice','uncertainty']:
        assert value[key]
    assert all(r['url'].startswith('https://extension.') for r in value['references'])
    if language=='ta':
        for key in ['title','explanation','scope','notice']:
            assert any('\u0b80'<=c<='\u0bff' for c in value[key])

@pytest.mark.parametrize('language',['en','ta'])
def test_low_confidence_suppresses_disease_guidance(monkeypatch,language):
    measured={'label':'early_blight','confidence':.4,'score':.4,'uncertain':True}
    monkeypatch.setattr(main,'classify_image',lambda raw:dict(measured))
    result=main.predict_image(b'unit-test-only',language)
    assert result['guidance'] is None
    assert all(result[k]==v for k,v in measured.items())

@pytest.mark.parametrize('label',['healthy','early_blight','late_blight'])
def test_language_changes_care_not_prediction(monkeypatch,label):
    measured={'label':label,'confidence':.9,'score':.9,'uncertain':False}
    monkeypatch.setattr(main,'classify_image',lambda raw:dict(measured))
    english=main.predict_image(b'unit-test-only','en')
    tamil=main.predict_image(b'unit-test-only','ta')
    assert all(english[k]==tamil[k]==v for k,v in measured.items())
    assert english['guidance']['language']=='en'
    assert tamil['guidance']['language']=='ta'
