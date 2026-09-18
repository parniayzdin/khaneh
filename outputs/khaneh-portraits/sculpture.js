'use strict';
(() => {
  const dialog = document.getElementById('sculptureDialog');
  const viewer = document.getElementById('hamidSculpture');
  const loading = document.getElementById('sculptureLoading');
  const controls = [...document.querySelectorAll('.sculpture-tools button')];
  controls.forEach(button => button.disabled = true);
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let trigger = null, loaded = false, opening = false, loadFailed = false, activeId = '';
  function fittedRadius() {
    const stage=document.getElementById('sculptureStage');
    const aspect=stage.clientWidth/Math.max(1,stage.clientHeight);
    // Frame the 2.16 m wide / 2.09 m high sculpture with space for its label.
    return Math.max(2.10,2.16/Math.max(.35,aspect))*.5/Math.tan(Math.PI/12)*1.28;
  }
  const defaultOrbit = () => `17deg 78deg ${fittedRadius()}m`;
  function enterCamera() {
    if (!loaded || !dialog.open) return;
    viewer.setAttribute('camera-orbit', reducedMotion.matches ? defaultOrbit() : `24deg 78deg ${fittedRadius()*1.35}m`);
    viewer.jumpCameraToGoal();
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if(dialog.open) viewer.setAttribute('camera-orbit', defaultOrbit());
    }));
  }
  viewer.addEventListener('load', () => { loaded = true; loading.hidden = true; controls.forEach(button => button.disabled = false); enterCamera(); });
  viewer.addEventListener('error', () => {
    loaded=false; loadFailed=true; controls.forEach(button => button.disabled = true);
    loading.hidden = false;
    loading.innerHTML = '<span>The sculpture could not load.</span>Try reopening it, or <a href="assets/sculpture/hamid-carrying-white.glb" download>download the 3D model</a>.';
  });
  window.openHamidSculpture = (person, source) => {
    if (opening || dialog.open) return;
    opening = true;
    trigger = source;
    const isKhodanoor=person.id==='khodanoor';
    const asset=isKhodanoor?'khodanoor-seated-white':'hamid-carrying-white';
    const changed=activeId!==person.id;activeId=person.id;
    dialog.dataset.personId=person.id;
    document.getElementById('sculptureName').textContent=person.name;
    dialog.querySelector('.sculpture-notes').setAttribute('aria-label',person.name+' — memory');
    const portrait=document.getElementById('sculpturePortrait');portrait.src=person.image;portrait.alt='Portrait of '+person.name;
    dialog.querySelector('.sculpture-identity span').textContent=person.persian;
    dialog.querySelector('.sculpture-identity p').textContent=isKhodanoor?'MEMORY 08':'MEMORY 05';
    dialog.querySelector('.sculpture-date').textContent=person.city+' · '+person.date;
    dialog.querySelector('.stage-heading p').textContent='IN REMEMBRANCE OF '+(isKhodanoor?'KHODANOOR':'HAMID');
    dialog.querySelector('.stage-heading h2').textContent=isKhodanoor?'Dignity, unbroken.':'To carry another.';
    dialog.querySelector('.sculpture-dedication').textContent=isKhodanoor?'A life beyond the image.':'A gesture of care, held in memory.';
    dialog.querySelector('.sculpture-caption').innerHTML='<strong>ABOUT THE SCULPTURE</strong>'+(isKhodanoor?'A simplified artistic interpretation of the supplied seated-pose drawing. The detention image predates his death; this is not a reconstruction of his final moments.':'An artistic interpretation of the supplied carrying-pose reference, in unpainted white. The pose and facial details are not a verified reconstruction.');
    dialog.querySelectorAll('a[download]').forEach(link=>{link.href='assets/sculpture/'+asset+(link.href.endsWith('.blend')?'.blend':'.glb');});
    viewer.alt=isKhodanoor?'White memorial study of a seated man with bowed head, raised knees, and hands restrained beside a pole.':'White memorial sculpture of a man carrying another person.';
    document.getElementById('sculptureStory').textContent = person.story;
    document.getElementById('sculptureSources').replaceChildren(...person.sources.map(record => {
      const link = document.createElement('a');
      link.href=record.url; link.target='_blank'; link.rel='noopener noreferrer'; link.textContent=record.title+' ↗'; return link;
    }));
    const image = source?.querySelector('img');
    const start = image?.getBoundingClientRect();
    dialog.showModal();
    document.body.style.overflow = 'hidden';
    dialog.querySelector('.sculpture-layout').scrollTop=0;
    if (changed || !viewer.hasAttribute('src') || loadFailed) {
      loaded=false;controls.forEach(button=>button.disabled=true);
      loading.hidden=false;
      loading.innerHTML='<span>Entering the sculpture room</span>Preparing the white sculpture…';
      viewer.setAttribute('src','assets/sculpture/'+asset+'.glb'+(loadFailed?'?retry='+Date.now():''));
      loadFailed=false;
    }
    if(loaded) enterCamera();
    if (start && !reducedMotion.matches) {
      const end = document.getElementById('sculpturePortrait').getBoundingClientRect();
      const clone = image.cloneNode();
      clone.removeAttribute('id'); clone.alt=''; clone.setAttribute('aria-hidden','true'); clone.className='sculpture-origin-image';
      Object.assign(clone.style,{left:start.left+'px',top:start.top+'px',width:start.width+'px',height:start.height+'px'});
      dialog.appendChild(clone);
      const animation = clone.animate([
        {transform:'translate(0,0) scale(1)',opacity:1},
        {transform:`translate(${end.left-start.left}px,${end.top-start.top}px) scale(${end.width/start.width},${end.height/start.height})`,opacity:0}
      ],{duration:700,easing:'cubic-bezier(.16,1,.3,1)',fill:'forwards'});
      animation.finished.then(()=>clone.remove(),()=>clone.remove());
    }
    opening=false;
  };
  document.getElementById('closeSculpture').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{
    document.body.style.overflow='';
    dialog.querySelectorAll('.sculpture-origin-image').forEach(image=>image.remove());
    trigger?.focus({preventScroll:true});
  });
  document.getElementById('resetSculpture').addEventListener('click',()=>{
    viewer.setAttribute('camera-orbit',defaultOrbit()); viewer.setAttribute('camera-target','auto auto auto');
    if(loaded) requestAnimationFrame(()=>viewer.jumpCameraToGoal());
  });
  new ResizeObserver(()=>{
    if(loaded && dialog.open){viewer.setAttribute('camera-orbit',defaultOrbit());}
  }).observe(document.getElementById('sculptureStage'));
  document.querySelectorAll('[data-sculpture-rotate],[data-sculpture-zoom]').forEach(button=>button.addEventListener('click',()=>{
    if (!loaded) return;
    const orbit=viewer.getCameraOrbit();
    const theta=orbit.theta*180/Math.PI+(Number(button.dataset.sculptureRotate)||0);
    const radius=orbit.radius*(Number(button.dataset.sculptureZoom)||1);
    viewer.setAttribute('camera-orbit',`${theta}deg ${orbit.phi*180/Math.PI}deg ${radius}m`);
    if(reducedMotion.matches) viewer.jumpCameraToGoal();
  }));
})();

