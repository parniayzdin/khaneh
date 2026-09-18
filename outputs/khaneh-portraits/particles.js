'use strict';
// Separate WebGL point study. The original model-viewer and sculpture stay intact.
(() => {
  const dialog = document.getElementById('sculptureDialog');
  const stage = document.getElementById('sculptureStage');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const panel = document.createElement('div');
  panel.className = 'particle-panel';
  panel.innerHTML = `<canvas tabindex="0" aria-label="Particle sculpture. Drag or use arrow keys to rotate; scroll or use plus and minus to zoom."></canvas>
    <p class="particle-status" role="status">Gathering the fragments…</p>
    <div class="particle-controls"><button data-action="pause">Pause motion</button><label>Dots <input aria-label="Dot density" type="range" min="12000" max="48000" value="40000" step="1000"></label><button data-action="reset">Reset view</button></div>
    <p class="particle-hint">Drag to turn · Scroll to zoom · A gesture, held in fragments</p>`;
  stage.append(panel);
  const tabs = document.createElement('div');
  tabs.className = 'sculpture-modes';
  tabs.setAttribute('role', 'group'); tabs.setAttribute('aria-label', 'Sculpture appearance');
  tabs.innerHTML = '<button aria-pressed="true" data-mode="particles">Particles</button><button aria-pressed="false" data-mode="solid">White statue</button>';
  stage.append(tabs);
  const canvas = panel.querySelector('canvas'), status = panel.querySelector('.particle-status');
  const pause = panel.querySelector('[data-action="pause"]');
  let mode = 'particles', running = !reduced.matches, ready = false, failed = false;
  let frame = 0, time = 0, previous = 0, yaw = .29, pitch = .12, zoom = 1, count = 40000;
  let gl, program, uniforms, initialization;
  const vertex = `
    attribute vec3 position; attribute vec3 normal; attribute vec2 variation;
    uniform float time, yaw, pitch, aspect, scale, pixelRatio, dotSize;
    varying float shade, opacity;
    void main() {
      float seed=variation.x*6.283185;
      float halo=variation.y;
      float drift=.0025 + halo*.3;
      vec3 p=position + vec3(sin(time*.55+seed),cos(time*.42+seed*2.),sin(time*.38+seed*3.))*drift;
      float cy=cos(yaw), sy=sin(yaw), cp=cos(pitch), sp=sin(pitch);
      vec3 r=vec3(cy*p.x+sy*p.z,p.y,-sy*p.x+cy*p.z);
      r=vec3(r.x,cp*r.y-sp*r.z,sp*r.y+cp*r.z);
      float depth=4.8-r.z;
      gl_Position=vec4(r.x*scale/aspect,r.y*scale, (depth-4.8)*.1,1.);
      gl_PointSize=clamp(dotSize*pixelRatio*(4.8/depth)*(1.-min(halo,.4)),1.,6.);
      vec3 n=vec3(cy*normal.x+sy*normal.z,normal.y,-sy*normal.x+cy*normal.z);
      shade=.16+.34*max(0.,dot(n,normalize(vec3(-.4,.7,1.))));
      opacity=(.65+.3*variation.x)*exp(-halo*6.);
    }`;
  const fragment = `precision mediump float;
    varying float shade, opacity;
    void main(){vec2 p=gl_PointCoord*2.-1.;float r=dot(p,p);if(r>1.)discard;
      float alpha=(1.-smoothstep(.65,1.,r))*opacity;
      gl_FragColor=vec4(vec3(shade),alpha);}`;
  function shader(type, text) {
    const result = gl.createShader(type); gl.shaderSource(result,text); gl.compileShader(result);
    if (!gl.getShaderParameter(result,gl.COMPILE_STATUS)) throw Error(gl.getShaderInfoLog(result));
    return result;
  }
  async function initialize() {
    try {
      gl=canvas.getContext('webgl',{alpha:false,antialias:true,preserveDrawingBuffer:false});
      if(!gl) throw Error('WebGL unavailable');
      program=gl.createProgram();
      gl.attachShader(program,shader(gl.VERTEX_SHADER,vertex));
      gl.attachShader(program,shader(gl.FRAGMENT_SHADER,fragment));
      gl.linkProgram(program);
      if(!gl.getProgramParameter(program,gl.LINK_STATUS)) throw Error('Shader link failed');
      gl.useProgram(program);
      const response=await fetch('assets/sculpture/hamid-particles.json');
      if(!response.ok) throw Error('Point data unavailable');
      const data=await response.json();
      if(data.count!==48000 || data.points.length!==data.count*8) throw Error('Invalid point data');
      const buffer=gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER,buffer);
      gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(data.points),gl.STATIC_DRAW);
      for(const [name,size,offset] of [['position',3,0],['normal',3,12],['variation',2,24]]) {
        const location=gl.getAttribLocation(program,name); gl.enableVertexAttribArray(location);
        gl.vertexAttribPointer(location,size,gl.FLOAT,false,32,offset);
      }
      uniforms=Object.fromEntries(['time','yaw','pitch','aspect','scale','pixelRatio','dotSize'].map(name=>[name,gl.getUniformLocation(program,name)]));
      gl.clearColor(1,1,1,1); gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
      gl.enable(gl.DEPTH_TEST);
      ready=true; status.hidden=true; update();
    } catch(error) {
      failed=true; status.hidden=false; status.textContent='The particle view could not load. Choose White statue to view the original.';
      console.error('Particle view:',error);
    }
  }
  function draw(now) {
    frame=0;
    if(!ready || failed || !dialog.open || mode!=='particles' || document.hidden) return;
    if(running && previous) time+=Math.min((now-previous)/1000,.05);
    previous=now;
    const width=panel.clientWidth,height=panel.clientHeight,dpr=Math.min(devicePixelRatio||1,2);
    if(!width||!height)return;
    const w=Math.round(width*dpr), h=Math.round(height*dpr);
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
    gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
    const drawingHeight=Math.max(120,height-195);
    gl.viewport(0,Math.round(80*dpr),w,Math.round(drawingHeight*dpr));
    const aspect=width/drawingHeight;
    const values={time,yaw,pitch,aspect,scale:Math.min(.78,aspect*.72)*zoom,pixelRatio:dpr,dotSize:1.35};
    for(const [key,value] of Object.entries(values))gl.uniform1f(uniforms[key],value);
    gl.drawArrays(gl.POINTS,0,count);
    if(running) frame=requestAnimationFrame(draw);
  }
  function update(){cancelAnimationFrame(frame);previous=0;if(ready&&!failed)frame=requestAnimationFrame(draw);}
  function select(next) {
    mode=next;stage.classList.toggle('show-particles',mode==='particles');panel.hidden=mode!=='particles';
    tabs.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
    if(mode==='particles'&&dialog.open&&!initialization)initialization=initialize();
    update();
  }
  tabs.addEventListener('click',event=>{if(event.target.dataset.mode)select(event.target.dataset.mode);});
  new MutationObserver(()=>{if(dialog.open)select(mode);else{cancelAnimationFrame(frame);previous=0;}}).observe(dialog,{attributes:true,attributeFilter:['open']});
  function updatePause(){pause.textContent=running?'Pause motion':'Resume motion';pause.setAttribute('aria-pressed',String(!running));}
  pause.addEventListener('click',()=>{running=!running;updatePause();update();});
  reduced.addEventListener('change',()=>{running=!reduced.matches;updatePause();update();});
  panel.querySelector('[data-action="reset"]').addEventListener('click',()=>{yaw=.29;pitch=.12;zoom=1;update();});
  panel.querySelector('input').addEventListener('input',event=>{count=Number(event.target.value);update();});
  let drag=null;
  canvas.addEventListener('pointerdown',event=>{drag={x:event.clientX,y:event.clientY,id:event.pointerId};canvas.setPointerCapture(event.pointerId);canvas.focus({preventScroll:true});});
  canvas.addEventListener('pointermove',event=>{if(!drag||event.pointerId!==drag.id)return;yaw+=(event.clientX-drag.x)*.006;pitch=Math.max(-1.1,Math.min(1.1,pitch+(event.clientY-drag.y)*.006));drag.x=event.clientX;drag.y=event.clientY;update();});
  canvas.addEventListener('lostpointercapture',()=>drag=null);
  canvas.addEventListener('pointerup',()=>drag=null);
  canvas.addEventListener('pointercancel',()=>drag=null);
  canvas.addEventListener('wheel',event=>{event.preventDefault();zoom=Math.max(.65,Math.min(2.5,zoom*Math.exp(-event.deltaY*.001)));update();},{passive:false});
  canvas.addEventListener('keydown',event=>{
    if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','+','=','-'].includes(event.key))return;
    event.preventDefault();if(event.key==='ArrowLeft')yaw-=.1;if(event.key==='ArrowRight')yaw+=.1;
    if(event.key==='ArrowUp')pitch=Math.max(-1.1,pitch-.1);if(event.key==='ArrowDown')pitch=Math.min(1.1,pitch+.1);
    if(event.key==='+'||event.key==='=')zoom=Math.min(2.5,zoom*1.1);if(event.key==='-')zoom=Math.max(.65,zoom/1.1);update();
  });
  canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();failed=true;cancelAnimationFrame(frame);status.hidden=false;status.textContent='Graphics paused. Reload the page or choose White statue.';});
  document.addEventListener('visibilitychange',update);
  new ResizeObserver(update).observe(stage);
  updatePause();select(mode);
})();
