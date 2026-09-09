(function(){
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* scroll reveal: opt in only when we can guarantee we can undo it */
  var nodes = [].slice.call(document.querySelectorAll('.reveal'));
  function showAll(){ nodes.forEach(function(n){ n.classList.add('in'); }); }
  if ('IntersectionObserver' in window && !reduce){
    document.documentElement.classList.add('js-reveal');
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
    },{rootMargin:'0px 0px -10% 0px'});
    nodes.forEach(function(n){ io.observe(n); });
    /* failsafe: nothing stays hidden because an observer never fired */
    setTimeout(showAll, 2500);
    addEventListener('beforeprint', showAll);
  }

  /* signature interaction: the field */
  if (reduce) return;
  var cv = document.getElementById('cv');
  if (!cv) return; /* the log pages carry no field */
  var gl = cv.getContext('webgl',{antialias:false,alpha:true,powerPreference:'low-power'});
  if (!gl) return;

  var VS = 'attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}';
  var FS = [
  'precision highp float;',
  'uniform vec2 R;uniform float T;uniform vec2 M;uniform float E;',
  'float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}',
  'float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);',
  ' return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}',
  'float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*n(p);p*=2.03;a*=.5;}return v;}',
  'void main(){',
  ' vec2 uv=gl_FragCoord.xy/R.xy;',
  ' vec2 q=uv;q.x*=R.x/R.y;',
  ' vec2 md=(M-.5)*vec2(R.x/R.y,1.);',
  ' float d=length(q-md-vec2(.5*R.x/R.y,.5));',
  ' float warp=.32/(1.+d*7.);',
  ' float t=T*.016;',
  ' vec2 f=q*1.45+vec2(t,-t*.6);',
  ' f+=warp*vec2(cos(d*5.-T*.16),sin(d*5.-T*.16));',
  ' float a=fbm(f);',
  ' float b=fbm(f*1.8+vec2(a*1.2,-a*.9)+vec2(0.,t*1.2));',
  ' float ridge=abs(b-.5)*2.;',
  ' float streams=pow(1.-ridge,5.5);',
  ' float haze=smoothstep(.30,.78,b);',
  /* deep ground that breathes, lilac carried mostly as haze */
  ' vec3 col=mix(vec3(.028,.034,.072),vec3(.062,.070,.150),a);',
  ' col+=vec3(.286,.290,.965)*haze*.30*smoothstep(1.15,.30,uv.x+uv.y*.30);',
  ' col+=vec3(.42,.46,1.)*streams*.16*smoothstep(1.05,.35,uv.x+uv.y*.30);',
  /* ember pole, lower right, lifted by E */
  ' float pole=smoothstep(.80,.06,length((uv-vec2(.93,.12))*vec2(1.30,1.15)));',
  ' col*=1.-pole*.42;',
  ' col+=vec3(1.,.400,.220)*pole*(.34+E*.46)*(.70+streams*.45);',
  /* dark corner where the type sits */
  ' col*=mix(.42,1.,smoothstep(.0,.95,uv.x*.75+uv.y*.55));',
  /* film grain */
  ' col+=(h(gl_FragCoord.xy+fract(T)*97.)-.5)*.045;',
  ' gl_FragColor=vec4(col,1.);',
  '}'].join('\n');

  function sh(t,s){var o=gl.createShader(t);gl.shaderSource(o,s);gl.compileShader(o);
    return gl.getShaderParameter(o,gl.COMPILE_STATUS)?o:null;}
  var vs=sh(gl.VERTEX_SHADER,VS), fs=sh(gl.FRAGMENT_SHADER,FS);
  if(!vs||!fs) return;
  var pr=gl.createProgram();gl.attachShader(pr,vs);gl.attachShader(pr,fs);gl.linkProgram(pr);
  if(!gl.getProgramParameter(pr,gl.LINK_STATUS)) return;
  gl.useProgram(pr);

  var buf=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buf);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,3,-1,-1,3]),gl.STATIC_DRAW);
  var loc=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);

  var uR=gl.getUniformLocation(pr,'R'),uT=gl.getUniformLocation(pr,'T'),
      uM=gl.getUniformLocation(pr,'M'),uE=gl.getUniformLocation(pr,'E');

  var host=document.getElementById('field'), mx=.62,my=.5,tx=.62,ty=.5,ember=0,tEmber=0,vis=true;

  function size(){
    var dpr=Math.min(window.devicePixelRatio||1,1.75);
    var w=host.clientWidth,hh=host.clientHeight;
    cv.width=Math.round(w*dpr);cv.height=Math.round(hh*dpr);
    gl.viewport(0,0,cv.width,cv.height);
  }
  size();
  addEventListener('resize',size,{passive:true});

  addEventListener('pointermove',function(e){
    var r=host.getBoundingClientRect();
    if(e.clientY>r.bottom) return;
    tx=e.clientX/r.width; ty=1-e.clientY/r.height;
  },{passive:true});

  addEventListener('deviceorientation',function(e){
    if(e.gamma==null) return;
    tx=.5+Math.max(-1,Math.min(1,e.gamma/45))*.42;
    ty=.5+Math.max(-1,Math.min(1,(e.beta-45)/45))*.32;
  },{passive:true});

  document.querySelectorAll('.btn--primary').forEach(function(b){
    b.addEventListener('pointerenter',function(){tEmber=1;});
    b.addEventListener('pointerleave',function(){tEmber=0;});
    b.addEventListener('focus',function(){tEmber=1;});
    b.addEventListener('blur',function(){tEmber=0;});
  });

  var t0=performance.now(), raf=0;

  function frame(now){
    raf=requestAnimationFrame(frame);
    mx+=(tx-mx)*.045; my+=(ty-my)*.045; ember+=(tEmber-ember)*.07;
    gl.uniform2f(uR,cv.width,cv.height);
    gl.uniform1f(uT,(now-t0)/1000);
    gl.uniform2f(uM,mx,my);
    gl.uniform1f(uE,ember);
    gl.drawArrays(gl.TRIANGLES,0,3);
  }
  /* the field costs GPU on a phone, so it only runs while it is actually on screen */
  function run(on){
    if(on && !raf){ raf=requestAnimationFrame(frame); }
    else if(!on && raf){ cancelAnimationFrame(raf); raf=0; }
  }
  new IntersectionObserver(function(e){
    vis=e[0].isIntersecting; run(vis && !document.hidden);
  },{threshold:0}).observe(host);
  document.addEventListener('visibilitychange',function(){ run(vis && !document.hidden); });

  raf=requestAnimationFrame(frame);
  host.classList.add('on');
})();
