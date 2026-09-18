'use strict';
const {people,geometry,art} = window.KHANEH;
const $ = selector => document.querySelector(selector);
const escapeHTML = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cities = {
  Tehran:{fa:'تهران',coord:[51.389,35.689]},
  Karaj:{fa:'کرج',coord:[50.967,35.840]},
  Izeh:{fa:'ایذه',coord:[49.867,31.833]},
  Mashhad:{fa:'مشهد',coord:[59.616,36.297]},
  Zahedan:{fa:'زاهدان',coord:[60.862,29.497]}
};
const project = ([lon,lat]) => [345+(lon-44)*27,120+(40-lat)*30.5];
const slots = [{x:36,y:1,r:2},{x:7,y:13,r:-3},{x:7,y:52,r:2},{x:27,y:65,r:-2},{x:79,y:6,r:3},{x:79,y:37,r:-2},{x:58,y:2,r:-2},{x:67,y:66,r:2},{x:47,y:66,r:2}];
let lastTrigger = null;

function drawMap(){
  const rings=geometry.type==='Polygon'?geometry.coordinates:geometry.coordinates.flat();
  const path=rings.map(ring=>ring.map((coord,i)=>`${i?'L':'M'}${project(coord).map(n=>n.toFixed(2)).join(',')}`).join(' ')+'Z').join(' ');
  $('#mapLayer').innerHTML=`<defs><clipPath id="iranClip"><path d="${path}"/></clipPath><pattern id="hatching" width="9" height="9" patternUnits="userSpaceOnUse"><path d="M0 9L9 0" stroke="#bca277" stroke-width=".5" opacity=".16"/></pattern></defs><path class="iran-outline" d="${path}"/><path fill="url(#hatching)" d="${path}"/><g clip-path="url(#iranClip)" class="map-contour">${Array.from({length:11},(_,i)=>`<path d="M${310+i*12} ${170+i*25}Q${510+i*12} ${130+i*21} ${700+i*8} ${360+i*18}T950 590"/>`).join('')}</g><text class="sea-label" x="575" y="192">Caspian Sea</text><text class="sea-label" x="480" y="540" transform="rotate(24 480 540)">Persian Gulf</text><text class="neighbor-label" x="770" y="130">TURKMENISTAN</text><text class="neighbor-label" x="940" y="382">AFGHANISTAN</text><text class="neighbor-label" x="332" y="322">IRAQ</text>`;
  $('#cityPins').innerHTML=Object.entries(cities).map(([city,p])=>{
    const [x,y]=project(p.coord);
    return `<button class="map-city" data-city="${city}" style="left:${x/12}%;top:${y/7.2}%" aria-label="Show memories from ${city}"><span class="city-dot"></span><span class="city-label">${city}</span></button>`;
  }).join('');
  $('#threads').innerHTML=people.map((p,i)=>{
    const slot=slots[i%slots.length],end=project(cities[p.city].coord),start=[slot.x*12+82,slot.y*7.2+10];
    return `<path class="memory-thread" data-thread="${p.id}" d="M${start[0]} ${start[1]} Q${(start[0]+end[0])/2} ${(start[1]+end[1])/2+45} ${end[0]} ${end[1]}"/>`;
  }).join('');
  Object.keys(cities).sort().forEach(city=>$('#cityFilter').add(new Option(city,city)));
  document.querySelectorAll('.map-city').forEach(button=>button.addEventListener('click',()=>{
    $('#cityFilter').value=$('#cityFilter').value===button.dataset.city?'':button.dataset.city;
    render();
  }));
}

function makeCard(p,i){
  const s=slots[i%slots.length];
  return `<button class="memory-card" data-id="${p.id}" style="--x:${s.x}%;--y:${s.y}%;--r:${s.r}deg" aria-label="Read the story of ${escapeHTML(p.name)}"><span class="card-photo"><img class="card-image" src="${escapeHTML(p.image)}" alt="Portrait of ${escapeHTML(p.name)}" decoding="async"></span><span class="card-label"><span>MEMORY ${String(i+1).padStart(2,'0')}</span><span>${['hamid','khodanoor'].includes(p.id)?'3D ↗':'↗'}</span></span><strong class="card-name">${escapeHTML(p.name)}</strong><span class="card-place">${escapeHTML(p.city)} · ${p.year}</span></button>`;
}
function render(){
  const query=$('#search').value.trim().toLocaleLowerCase(),city=$('#cityFilter').value;
  const visible=people.filter(p=>(!city||p.city===city)&&`${p.name} ${p.persian} ${p.city} ${p.year} ${p.tags||''}`.toLocaleLowerCase().includes(query));
  const ids=new Set(visible.map(p=>p.id));
  $('#atlasViewport').hidden=!visible.length;
  $('#emptyState').hidden=!!visible.length;
  $('#atlasPortraits').innerHTML=people.map(makeCard).join('');
  document.querySelectorAll('.memory-card').forEach(card=>{
    const isVisible=ids.has(card.dataset.id);
    card.classList.toggle('is-dim',!isVisible);
    card.disabled=!isVisible;
    card.tabIndex=isVisible?0:-1;
    card.setAttribute('aria-hidden',String(!isVisible));
    card.addEventListener('click',()=>openMemory(card.dataset.id,card));
    const highlight=on=>document.querySelector(`[data-thread="${card.dataset.id}"]`)?.classList.toggle('highlight',on);
    card.addEventListener('mouseenter',()=>highlight(true));card.addEventListener('mouseleave',()=>highlight(false));
    card.addEventListener('focus',()=>highlight(true));card.addEventListener('blur',()=>highlight(false));
  });
  document.querySelectorAll('[data-thread]').forEach(path=>path.classList.toggle('is-dim',!ids.has(path.dataset.thread)));
  document.querySelectorAll('.map-city').forEach(pin=>{pin.classList.toggle('active',city===pin.dataset.city);pin.classList.toggle('is-dim',!visible.some(p=>p.city===pin.dataset.city));pin.setAttribute('aria-pressed',String(city===pin.dataset.city));});
  const countCities=new Set(visible.map(p=>p.city)).size;
  $('#resultCount').textContent=`${String(visible.length).padStart(2,'0')} ${visible.length===1?'remembered life':'remembered lives'} · ${countCities} ${countCities===1?'city':'cities'}${city?' · '+city:''}`;
  $('#resetFilters').hidden=!query&&!city;
}
function openMemory(id,trigger){
  const person=people.find(p=>p.id===id);if(!person)return;
  if(['hamid','khodanoor'].includes(id) && window.openHamidSculpture){window.openHamidSculpture(person,trigger);return;}
  lastTrigger=trigger;
  $('#memoryImage').src=person.image;$('#memoryImage').alt=`Portrait of ${person.name}`;
  $('#memoryName').textContent=person.name;$('#memoryPersian').textContent=person.persian;
  $('#memoryFacts').textContent=`${person.city} · ${person.date}`;
  $('#memoryStory').textContent=person.story;$('#memoryCity').textContent=person.city;
  $('#memorySources').innerHTML=person.sources.map(source=>`<a href="${escapeHTML(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(source.title)} ↗</a>`).join('');
  $('#photoCredit').textContent=person.credit;
  $('#memoryDialog').showModal();
}
function clearFilters(){$('#search').value='';$('#cityFilter').value='';render();}
function populateCredits(){
  $('#creditsContent').innerHTML=`<h3>People & their stories</h3><p>Portraits are reproduced from the linked source records for this private design preview. Copyright remains with the respective owners.</p><ul>${people.map(p=>`<li><strong>${escapeHTML(p.name)}</strong> — ${p.sources.map(s=>`<a href="${escapeHTML(s.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(s.title)}</a>`).join('; ')}<br>${escapeHTML(p.credit)}</li>`).join('')}</ul><h3>The painted pages</h3><p>Historical manuscript artwork from museum open-access collections.</p><ul>${art.map(a=>`<li><a href="${escapeHTML(a.source)}" target="_blank" rel="noopener noreferrer">${escapeHTML(a.title)}</a><br>${escapeHTML(a.date)} · ${escapeHTML(a.museum)} · ${escapeHTML(a.license)}</li>`).join('')}</ul><h3>Map</h3><p>Country outline: <a href="https://www.naturalearthdata.com/about/terms-of-use/" target="_blank" rel="noopener noreferrer">Natural Earth, public domain</a>. The outline is generalized. Pins use approximate city centers. The fine contour lines are decoration, not surveyed topography.</p>`;
}
$('#search').addEventListener('input',render);$('#cityFilter').addEventListener('change',render);
$('#resetFilters').addEventListener('click',clearFilters);$('#emptyReset').addEventListener('click',clearFilters);
$('#aboutButton').addEventListener('click',()=>$('#aboutDialog').showModal());$('#creditsButton').addEventListener('click',()=>$('#creditsDialog').showModal());
document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
document.querySelectorAll('dialog').forEach(dialog=>{dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();});});
$('#memoryDialog').addEventListener('close',()=>lastTrigger?.focus());
drawMap();populateCredits();render();
document.querySelector('#creditsContent').insertAdjacentHTML('beforeend','<h3>New miniature references</h3><p>The Persian court, garden, and palace paintings used in this study were supplied by the user as visual references. Attribution is to be confirmed.</p><h3>The white sculpture</h3><p>A new Blender study made for Khaneh, interpreted from the supplied carrying-pose image. It is not a verified reconstruction. Interactive viewer: <a href="https://modelviewer.dev/" target="_blank" rel="noopener noreferrer">Google model-viewer</a>, Apache-2.0.</p>');



