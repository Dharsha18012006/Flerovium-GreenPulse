"""Original concise bilingual guidance, adapted from extension sources in SOURCES.md."""
CARE = {
 'healthy': {
  'en': {'title': 'Healthy-pattern guidance', 'steps': ['Keep watering at soil level and check leaves regularly.', 'A photo cannot rule out other diseases, pests or nutrient problems.']},
  'ta': {'title': 'ஆரோக்கியமான இலைக்கான வழிகாட்டல்', 'steps': ['மண்ணில் நீர் ஊற்றவும். இலைகளைத் தொடர்ந்து கவனிக்கவும்.', 'படத்தை மட்டும் வைத்து மற்ற நோய்கள், பூச்சிகள் அல்லது ஊட்டச்சத்து குறைபாடுகளை நிராகரிக்க முடியாது.']},
  'source': 'https://extension.umn.edu/vegetables/growing-tomatoes'},
 'early_blight': {
  'en': {'title': 'Possible early blight', 'steps': ['Keep foliage dry; water at the base and improve airflow.', 'Remove affected lower leaves when dry; clean tools afterward.', 'Ask a local gardening or agricultural expert to confirm persistent symptoms.']},
  'ta': {'title': 'ஆரம்ப இலைக்கருகல் இருக்கலாம்', 'steps': ['இலைகள் ஈரமாகாமல் அடிப்பகுதியில் நீர் ஊற்றவும். காற்றோட்டத்தை அதிகரிக்கவும்.', 'உலர்ந்த நிலையில் பாதிக்கப்பட்ட கீழ் இலைகளை அகற்றி, கருவிகளைச் சுத்தம் செய்யவும்.', 'அறிகுறிகள் தொடர்ந்தால் உள்ளூர் தோட்டக்கலை அல்லது வேளாண் நிபுணரிடம் உறுதிப்படுத்தவும்.']},
  'source': 'https://www.extension.umd.edu/resource/early-blight-tomatoes'},
 'late_blight': {
  'en': {'title': 'Possible late blight — prompt expert review', 'steps': ['Avoid moving affected plants or wet foliage between gardens.', 'Contact a local agricultural expert promptly; similar symptoms need confirmation.', 'Keep leaves dry. Do not choose a pesticide from this prediction alone.']},
  'ta': {'title': 'பின்பருவ இலைக்கருகல் இருக்கலாம் — விரைவில் நிபுணரை அணுகவும்', 'steps': ['பாதிக்கப்பட்ட செடிகள் அல்லது ஈரமான இலைகளை மற்ற தோட்டங்களுக்கு எடுத்துச் செல்ல வேண்டாம்.', 'அறிகுறிகளை உறுதிப்படுத்த உள்ளூர் வேளாண் நிபுணரை விரைவில் அணுகவும்.', 'இலைகளை உலர்வாக வைத்திருக்கவும். இந்தக் கணிப்பை மட்டும் வைத்து பூச்சிக்கொல்லியைத் தேர்ந்தெடுக்க வேண்டாம்.']},
  'source': 'https://extension.umd.edu/resource/late-blight-tomato-and-potato'}
}

# Curated paraphrases; no runtime text generation. Source URLs above cover each entry.
DETAILS = {
 'healthy': {
  'en': {'explanation': 'A healthy-pattern result means the photo resembles healthy tomato leaves in the training set. It does not prove that the whole plant is healthy.', 'symptoms': ['Check for new spots, yellowing or wilting; these need attention even after a healthy-pattern result.'], 'prevention': ['Water consistently at soil level and support plants to keep leaves away from soil.']},
  'ta': {'explanation': 'ஆரோக்கியமான இலை என்ற முடிவு வந்தால், படம் பயிற்சித் தொகுப்பில் உள்ள ஆரோக்கியமான தக்காளி இலைகளை ஒத்துள்ளது என்று பொருள். செடி முழுவதும் ஆரோக்கியமாக இருப்பதை இது உறுதிப்படுத்தாது.', 'symptoms': ['புதிய புள்ளிகள், மஞ்சள் நிறமாற்றம் அல்லது வாடுதல் உள்ளதா என்று கவனிக்கவும். ஆரோக்கியமான இலை என்ற முடிவு வந்தாலும் இவற்றைக் கவனிக்க வேண்டும்.'], 'prevention': ['மண்ணில் சீராக நீர் ஊற்றவும். இலைகள் மண்ணைத் தொடாமல் செடிக்கு ஆதரவு அளிக்கவும்.']}},
 'early_blight': {
  'en': {'explanation': 'Early blight is a fungal disease that often starts on older, lower tomato leaves. Similar-looking damage can have other causes.', 'symptoms': ['Brown spots may have concentric rings and surrounding yellowing.'], 'prevention': ['Space plants for airflow; mulch soil to reduce splashing and water at the base.']},
  'ta': {'explanation': 'ஆரம்ப இலைக்கருகல் ஒரு பூஞ்சை நோய். இது பெரும்பாலும் தக்காளிச் செடியின் கீழ்ப்பகுதியில் உள்ள பழைய இலைகளில் தொடங்கும். இதே போன்ற பாதிப்புகளுக்கு வேறு காரணங்களும் இருக்கலாம்.', 'symptoms': ['பழுப்பு நிறப் புள்ளிகளில் வட்ட வளையங்களும், அவற்றைச் சுற்றி மஞ்சள் நிறமாற்றமும் தோன்றலாம்.'], 'prevention': ['காற்றோட்டத்திற்கு இடைவெளி விடவும். மண் தெறிப்பைக் குறைக்க மூடாக்கு இடவும். செடியின் அடியில் நீர் ஊற்றவும்.']}},
 'late_blight': {
  'en': {'explanation': 'Late blight is caused by a fungus-like water mold and can progress rapidly in cool, wet conditions. A photo match needs expert confirmation.', 'symptoms': ['Dark, water-soaked patches can expand on leaves or stems; white fuzzy growth may appear beneath leaves in damp conditions.'], 'prevention': ['Avoid overhead watering and crowded plants. Ask locally about suitable resistant varieties.']},
  'ta': {'explanation': 'பின்பருவ இலைக்கருகல் பூஞ்சை போன்ற நீர்ப்பூஞ்சையால் ஏற்படுகிறது. குளிர்ந்த, ஈரமான சூழலில் விரைவாகப் பரவலாம். படத்தின் முடிவை நிபுணரிடம் உறுதிப்படுத்த வேண்டும்.', 'symptoms': ['இலைகள் அல்லது தண்டுகளில் நீரில் நனைந்தது போன்ற கருமையான திட்டுகள் பெரிதாகலாம். ஈரமான சூழலில் இலைகளின் அடியில் வெள்ளைப் பஞ்சு போன்ற வளர்ச்சி தோன்றலாம்.'], 'prevention': ['இலைகளின் மேல் நீர் தெளிப்பதையும் செடிகளை நெருக்கமாக நடுவதையும் தவிர்க்கவும். பொருத்தமான நோய் எதிர்ப்பு ரகங்களைப் பற்றி உள்ளூர் நிபுணரிடம் கேட்கவும்.']}}
}
TEXT = {
 'en': {'scope': 'Only selected tomato-leaf categories are supported: healthy pattern, early blight and late blight. Other diseases and plants are not reliably recognized.', 'notice': 'Curated source-grounded guidance, not a diagnosis or a guaranteed cure. Do not select a pesticide or dosage from this result; consult a local agricultural expert.', 'uncertainty': 'Low confidence: this result is uncertain. Retake a clear photo of one tomato leaf or ask an agricultural expert. No disease-specific advice is inferred from this result.', 'translation_review': 'Tamil wording awaits human review.', 'headings': {'explanation':'What this means','symptoms':'Visible signs to check','prevention':'Basic prevention','steps':'Safe next steps','references':'References'}},
 'ta': {'scope': 'தக்காளி இலைகளின் மூன்று வகைகள் மட்டுமே ஆதரிக்கப்படுகின்றன: ஆரோக்கியமான இலை, ஆரம்ப இலைக்கருகல், பின்பருவ இலைக்கருகல். மற்ற நோய்களையும் தாவரங்களையும் நம்பகமாகக் கண்டறிய முடியாது.', 'notice': 'இது ஆதாரங்களின் அடிப்படையில் தொகுக்கப்பட்ட வழிகாட்டல் மட்டுமே; நோய் உறுதிப்படுத்தலோ குணமாகும் உத்தரவாதமோ அல்ல. இந்த முடிவை மட்டும் வைத்து பூச்சிக்கொல்லி அல்லது அதன் அளவைத் தேர்ந்தெடுக்க வேண்டாம்; உள்ளூர் வேளாண் நிபுணரை அணுகவும்.', 'uncertainty': 'நம்பகத்தன்மை குறைவு: இந்த முடிவு உறுதியற்றது. ஒரு தக்காளி இலையைத் தெளிவாக மீண்டும் படம் எடுக்கவும் அல்லது வேளாண் நிபுணரை அணுகவும். இந்த முடிவிலிருந்து நோய் சார்ந்த ஆலோசனை வழங்கப்படவில்லை.', 'translation_review': 'தமிழ் உரைக்கு மனித மதிப்பாய்வு இன்னும் தேவை.', 'headings': {'explanation':'இதன் பொருள்','symptoms':'கவனிக்க வேண்டிய அறிகுறிகள்','prevention':'அடிப்படைத் தடுப்பு','steps':'பாதுகாப்பான அடுத்த படிகள்','references':'ஆதாரங்கள்'}}
}
for condition, languages in DETAILS.items():
    for language, details in languages.items():
        CARE[condition][language].update(details)


def get_guidance(condition, language):
    source = CARE[condition]['source'].replace('www.extension.umd.edu', 'extension.umd.edu')
    title = {'healthy':'University of Minnesota Extension — Growing tomatoes', 'early_blight':'University of Maryland Extension — Early blight of tomatoes', 'late_blight':'University of Maryland Extension — Late blight of tomato and potato'}[condition]
    return {**CARE[condition][language], **TEXT[language], 'source':source,
            'references':[{'title':title,'url':source}], 'language':language,
            'content_type':'curated', 'generated':False, 'reviewed_sources_on':'2026-10-17'}
