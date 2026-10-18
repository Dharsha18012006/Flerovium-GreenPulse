/* Curated guidance rendering and a non-sensitive, browser-local preference. */
window.GreenPulseCare = (() => {
  const key = 'greenpulse.language';
  let language = 'en';
  try { const saved = localStorage.getItem(key); if (['en','ta'].includes(saved)) language = saved; } catch (_) {}
  function setLanguage(value) {
    language = ['en','ta'].includes(value) ? value : 'en';
    try { localStorage.setItem(key, language); } catch (_) {}
    document.querySelectorAll('#lang,#care-lang').forEach(select => select.value = language);
  }
  function node(tag, text) { const n = document.createElement(tag); n.textContent = text; return n; }
  function render(target, data) {
    target.lang = data.language;
    target.replaceChildren(node('small',data.language === 'ta' ? 'தொகுக்கப்பட்ட பராமரிப்பு வழிகாட்டல் · AI நோய் உறுதிப்படுத்தல் அல்ல' : 'CURATED CARE · Separate from the model prediction'),node('h3',data.title));
    target.append(node('h4',data.headings.explanation),node('p',data.explanation));
    for (const key of ['symptoms','prevention','steps']) {
      target.append(node('h4',data.headings[key]));
      const list = node('ul',''); data[key].forEach(text => list.append(node('li',text))); target.append(list);
    }
    target.append(node('p',data.scope),node('p',data.notice),node('h4',data.headings.references));
    data.references.forEach(source => {
      const link = node('a',source.title+' ↗'); link.href=source.url; link.target='_blank'; link.rel='noopener noreferrer'; target.append(link);
    });
    target.append(node('p',data.translation_review));
  }
  function uncertain(target) {
    target.lang=language;
    target.textContent=language==='ta'
      ? 'நம்பகத்தன்மை குறைவு: இந்த முடிவு உறுதியற்றது. ஒரு தக்காளி இலையைத் தெளிவாக மீண்டும் படம் எடுக்கவும் அல்லது வேளாண் நிபுணரை அணுகவும். நோய் சார்ந்த ஆலோசனை வழங்கப்படவில்லை. இந்த வகைப்படுத்தி தக்காளி இலைகளின் மூன்று வகைகளை மட்டுமே ஆதரிக்கிறது.'
      : 'Low confidence: this result is uncertain. Retake a clear photo of one tomato leaf or ask an agricultural expert. No disease-specific advice is inferred. Only three tomato-leaf categories are supported.';
  }
  setLanguage(language);
  return {render, uncertain, setLanguage, get language(){return language;}};
})();
