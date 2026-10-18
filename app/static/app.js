const $=s=>document.querySelector(s);
async function api(path,options={}){let r;try{r=await fetch('/api/'+path,{...options,signal:AbortSignal.timeout(45000)});}catch(e){throw Error(e.name==='TimeoutError'?'The request timed out. Please try again.':'Cannot reach GreenPulse. Check your connection and SSH tunnel, then retry.');}const data=await r.json();if(!r.ok)throw Error(typeof data.detail==='string'?data.detail:'Please check all fields.');return data;}
function el(tag,text){const n=document.createElement(tag);n.textContent=text;return n;}
function note(text){$('#notice').textContent=text;}
async function run(button,fn){const original=button.textContent;button.disabled=true;button.textContent='Please wait…';button.setAttribute('aria-busy','true');note('');try{await fn();}catch(e){note(e.message);}finally{button.disabled=false;button.textContent=original;button.removeAttribute('aria-busy');}}
function guidance(target,data){GreenPulseCare.render(target,data);}
let listingVersion=0;
function dated(text){return el('p',text+' UTC');}
async function loadPosts(){
  const posts=await api('posts'), box=$('#posts');box.replaceChildren();
  if(!posts.length)box.append(el('p','No posts yet. Start the conversation.'));
  for(const post of posts){const card=el('article','');card.append(el('strong',post.author),el('p',post.body),dated(post.created));box.append(card);}
}
async function loadListings(){
  const version=++listingVersion, box=$('#listings');box.textContent='Loading listings…';
  const params=new URLSearchParams({q:$('#market-query').value.trim()});
  if($('#market-category').value)params.set('category',$('#market-category').value);
  try{
    const listings=await api('listings?'+params);if(version!==listingVersion)return;box.replaceChildren();
    if(!listings.length)box.append(el('p','No matching listings. Clear filters or create the first listing.'));
    for(const item of listings){const card=el('article','');card.append(el('small',item.category),el('h4',item.title),el('p',item.price===null?'Price not specified':`₹${item.price}`),el('p',item.description),el('p',item.area),dated(item.created));if(item.contact_consent && item.seller_email){const contact=el('a','Email seller: '+item.seller_email);contact.href='mailto:'+encodeURIComponent(item.seller_email);card.append(contact);}else{card.append(el('p','Seller has not shared a contact email.'));}box.append(card);}
  }catch(err){if(version===listingVersion)box.textContent='Listings unavailable. Use Search listings to retry.';throw err;}
}
async function loadSignals(){
  const data=await api('signals'), box=$('#signal-list');box.replaceChildren(el('p',data.notice));
  if(!data.signals.length)box.append(el('p','No groups meet the five-report display threshold yet.'));
  const maximum=Math.max(5,...data.signals.map(s=>s.reports));
  for(const signal of data.signals){
    const card=el('article','');
    card.append(el('small',signal.simulated?'SIMULATED DEMONSTRATION':'UNVERIFIED VOLUNTARY REPORTS'),el('h4',signal.area+' · '+signal.condition.replaceAll('_',' ')),el('p',signal.reports+' reports'),el('p',`${signal.first_date} to ${signal.last_date} (UTC)`));
    const bar=el('meter','');bar.min=0;bar.max=maximum;bar.value=signal.reports;bar.setAttribute('aria-label',signal.reports+' unverified reports');card.append(bar);box.append(card);
  }
}
async function refresh(){
  const tasks=[loadPosts(),loadListings(),loadSignals()], boxes=['#posts','#listings','#signal-list'];
  const results=await Promise.allSettled(tasks);
  results.forEach((result,i)=>{if(result.status==='rejected'){$(boxes[i]).textContent='Unable to load this section. Refresh to retry.';note(result.reason.message);}});
}
$('#market-search').onsubmit=e=>{e.preventDefault();run(e.submitter,loadListings);};
$('#market-reset').onclick=e=>run(e.target,async()=>{$('#market-search').reset();await loadListings();});
for(const [form,path] of [['post','posts'],['listing','listings'],['report','reports']]){
  $('#'+form).addEventListener('submit',e=>{
    e.preventDefault();run(e.submitter,async()=>{
      const values=Object.fromEntries(new FormData(e.target));
      if(form==='post')values.author=values.author.trim()||'Anonymous gardener';
      if(form==='listing'){values.price=values.price.trim()===''?null:Number(values.price);values.contact_consent=e.target.elements.contact_consent.checked;if(Boolean(values.seller_email.trim())!==values.contact_consent)throw Error('To share contact details, enter an email and select the sharing consent box.');}
      if(form==='report'){values.consent=e.target.elements.consent.checked;values.simulated=e.target.elements.simulated.checked;}
      await api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(values)});
      e.target.reset();note(form==='report'?'Observation saved. Small groups remain hidden; simulated reports stay separate.':'Saved.');
      if(form==='listing')$('#market-search').reset();
      await refresh();
    });
  });
}
let previewURL, generation=0, lastPrediction=null, careVersion=0, libraryVersion=0;
const names={healthy:'Tomato Healthy',early_blight:'Tomato Early Blight',late_blight:'Tomato Late Blight'};
$('#photo').onchange=()=>{generation++;lastPrediction=null;careVersion++;if(previewURL)URL.revokeObjectURL(previewURL);const f=$('#photo').files[0];$('#preview').hidden=true;$('#prediction').className='';$('#prediction').textContent='Ready to check your selected leaf.';if(f&&f.size<=5*1024*1024&&['image/jpeg','image/png'].includes(f.type)){previewURL=URL.createObjectURL(f);$('#preview').src=previewURL;$('#preview').hidden=false;}};
$('#preview').onerror=()=>{$('#preview').hidden=true;};
$('#predict').onsubmit=e=>{e.preventDefault();run(e.submitter,async()=>{const box=$('#prediction'),f=$('#photo').files[0],version=generation;lastPrediction=null;careVersion++;box.className='';try{if(!f||!f.size)throw Error('Choose a non-empty leaf photo.');if(f.size>5*1024*1024)throw Error('Choose an image smaller than 5 MB.');if(!['image/jpeg','image/png'].includes(f.type))throw Error('Unsupported format. Choose JPEG or PNG.');box.textContent='Checking your leaf on LinuxONE…';box.setAttribute('aria-busy','true');const r=await api('predict?lang='+$('#lang').value,{method:'POST',headers:{'Content-Type':f.type},body:f});if(version!==generation)return;box.className=r.uncertain?'result uncertain':'result';box.replaceChildren(el('small',r.uncertain?'UNCERTAIN RESULT':'EXPERIMENTAL PATTERN MATCH'),el('h3',names[r.label]),el('p',`Confidence (uncalibrated model score): ${(r.confidence*100).toFixed(1)}%`),el('p',r.message),el('p',r.limitations),el('small',`Processed on IBM LinuxONE · ${r.architecture} · Photo not saved`));const meter=el('meter','');meter.min=0;meter.max=1;meter.value=r.confidence;meter.setAttribute('aria-label','Uncalibrated model confidence');box.append(meter);lastPrediction=r;await renderPredictionCare();}catch(err){if(version===generation){box.className='result error';box.textContent=err.message;}throw err;}finally{box.removeAttribute('aria-busy');}});};
async function renderPredictionCare(){
  const version=++careVersion, result=lastPrediction;
  document.querySelector('#prediction .care-panel')?.remove();
  if(!result)return;
  const panel=el('div','');panel.className='care-panel';$('#prediction').append(panel);
  if(result.uncertain){GreenPulseCare.uncertain(panel);return;}
  panel.textContent=GreenPulseCare.language==='ta'?'வழிகாட்டல் ஏற்றப்படுகிறது…':'Loading curated guidance…';
  try{const data=await api('care/'+result.label+'?lang='+GreenPulseCare.language);if(version===careVersion)guidance(panel,data);}
  catch(err){if(version===careVersion)panel.textContent='Guidance unavailable. Use Read care to retry. '+err.message;}
}
async function loadLibrary(){
  const version=++libraryVersion;
  $('#care-result').textContent=GreenPulseCare.language==='ta'?'வழிகாட்டல் ஏற்றப்படுகிறது…':'Loading curated guidance…';
  try{const data=await api('care/'+$('#care-condition').value+'?lang='+GreenPulseCare.language);
    if(version===libraryVersion)guidance($('#care-result'),data);
  }catch(err){if(version===libraryVersion)$('#care-result').textContent='Guidance unavailable. Select Read care to retry. '+err.message;throw err;}
}
$('#care-button').onclick=e=>run(e.target,loadLibrary);
for(const select of [$('#lang'),$('#care-lang')])select.onchange=async()=>{
  GreenPulseCare.setLanguage(select.value);
  await Promise.all([renderPredictionCare(),loadLibrary().catch(err=>note(err.message))]);
};
$('#care-condition').onchange=()=>loadLibrary().catch(err=>note(err.message));
function mapLink(query){const a=$('#map-link');a.href='https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(query);a.hidden=false;$('#location-status').textContent='Search ready. Open Google Maps below.';}
$('#search-place').onclick=()=>{note('');$('#map-link').hidden=true;$('#location-status').textContent='';const place=$('#place').value.trim();if(!place)return note('Enter a city or neighbourhood.');mapLink('plant nurseries garden centres in '+place);};
$('#locate').onclick=()=>{$('#map-link').hidden=true;if(!navigator.geolocation)return note('Location is unavailable; enter an area instead.');$('#location-status').textContent='Waiting for location permission…';navigator.geolocation.getCurrentPosition(p=>mapLink(`plant nurseries near ${p.coords.latitude.toFixed(3)},${p.coords.longitude.toFixed(3)}`),()=>{$('#location-status').textContent='Location unavailable or permission declined. Enter an area instead.';},{enableHighAccuracy:false,timeout:10000,maximumAge:60000});};
api('health').then(h=>$('#health').textContent=h.architecture==='s390x'&&h.model_file_present?'LinuxONE connected':'Local development · inference requires LinuxONE').catch(()=>$('#health').textContent='Service unavailable');refresh();

function updateNavigation(){
  const current=location.hash||'#screen';
  document.querySelectorAll('nav a').forEach(link=>{
    if(link.getAttribute('href')===current)link.setAttribute('aria-current','location');
    else link.removeAttribute('aria-current');
  });
}
addEventListener('hashchange',updateNavigation);
updateNavigation();
