const COLORS = {
  grid: '#2d2d33', current: '#80dfff', ma: '#afd485', upper: '#e070c0', lower: '#afd485',
  tqqq: '#e8714f', spym: '#b07cc0', sgov: '#5bb8e8', neutral: '#aaaaaa', fear: '#f0a0a0',
  extremeFear: '#e8714f', greed: '#5bb8e8', extremeGreed: '#b07cc0', white: '#ffffff'
};
const $ = (id) => document.getElementById(id);

function fitCanvas(canvas) {
  const ratio = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = Math.round(rect.width * ratio);
  canvas.height = Math.round(rect.height * ratio);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return {ctx, w: rect.width, h: rect.height};
}

function drawLineChart(canvas, series, minOverride, maxOverride) {
  const {ctx,w,h}=fitCanvas(canvas); ctx.clearRect(0,0,w,h);
  const pad={l:8,r:8,t:10,b:12};
  const vals=series.flatMap(s=>s.values).filter(Number.isFinite);
  const min=minOverride ?? Math.min(...vals), max=maxOverride ?? Math.max(...vals), range=(max-min)||1;
  [0.25,0.5,0.75].forEach(p=>{ctx.strokeStyle=COLORS.grid;ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(pad.l,pad.t+(h-pad.t-pad.b)*p);ctx.lineTo(w-pad.r,pad.t+(h-pad.t-pad.b)*p);ctx.stroke();});
  series.forEach(s=>{ctx.strokeStyle=s.color;ctx.lineWidth=s.width||2;ctx.beginPath();let started=false;s.values.forEach((v,i)=>{if(!Number.isFinite(v))return;const x=pad.l+(i/(s.values.length-1||1))*(w-pad.l-pad.r);const y=h-pad.b-((v-min)/range)*(h-pad.t-pad.b);if(!started){ctx.moveTo(x,y);started=true}else ctx.lineTo(x,y)});ctx.stroke();});
}

function fgiColor(v){if(v>=75)return COLORS.extremeGreed;if(v>=55)return COLORS.greed;if(v>=45)return COLORS.neutral;if(v>=25)return COLORS.fear;return COLORS.extremeFear}
function drawFgiChart(canvas, values){drawLineChart(canvas,[{values,color:'rgba(255,255,255,.45)',width:2}],0,100);const {ctx,w,h}=fitCanvas(canvas);const pad={l:8,r:8,t:10,b:12};values.forEach((v,i)=>{const x=pad.l+(i/(values.length-1||1))*(w-pad.l-pad.r);const y=h-pad.b-(v/100)*(h-pad.t-pad.b);ctx.fillStyle=fgiColor(v);ctx.beginPath();ctx.arc(x,y,3.2,0,Math.PI*2);ctx.fill();});}
function drawGauge(canvas,value){const {ctx,w,h}=fitCanvas(canvas);ctx.clearRect(0,0,w,h);const cx=w/2,cy=h*.92,r=Math.min(w*.42,h*.78);for(let i=0;i<120;i++){const t=i/119,a=Math.PI+t*Math.PI;ctx.fillStyle=fgiColor(t*100);ctx.beginPath();ctx.arc(cx+Math.cos(a)*r,cy+Math.sin(a)*r,4.6,0,Math.PI*2);ctx.fill();}const a=Math.PI+(value/100)*Math.PI;ctx.strokeStyle='#fff';ctx.lineWidth=5;ctx.lineCap='round';ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+Math.cos(a)*(r-7),cy+Math.sin(a)*(r-7));ctx.stroke();ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(cx,cy,6,0,Math.PI*2);ctx.fill();}

function tokenClass(name){return name==='TQQQ'?'token-tqqq':name==='SPYM'?'token-spym':name==='SGOV'?'token-sgov':''}
function renderActions(target, lines, isAlert=false){target.innerHTML='';lines.forEach(([asset,action])=>{const row=document.createElement('div');row.className='action-line'+(isAlert?' alert':'');asset.split('·').forEach((part,i)=>{const span=document.createElement('span');span.className=tokenClass(part);span.textContent=part;row.appendChild(span);if(i<asset.split('·').length-1)row.append('·')});const actionSpan=document.createElement('span');actionSpan.textContent=action;row.appendChild(actionSpan);target.appendChild(row);});}
function money(v){return Number.isFinite(v)?`$${v.toFixed(2)}`:'-'}

async function load(){
  try{
    const res=await fetch(`data/latest.json?v=${Date.now()}`); if(!res.ok)throw new Error(`HTTP ${res.status}`); const d=await res.json();
    $('updatedAt').textContent=`최종 갱신: ${d.updated_at_kst}`;$('marketDate').textContent=`${d.market_date} 미국장 종가 기준`;
    const beta=d.beta;renderActions($('betaActions'),beta.signal.lines,beta.signal.is_alert);$('betaStatus').textContent=beta.signal.name;$('betaStatus').classList.toggle('alert',beta.signal.is_alert);$('drawdown').textContent=beta.signal.drawdown_text;$('qqqPrice').textContent=money(beta.current_price);$('qqqSma').textContent=money(beta.sma_200);
    drawLineChart($('betaChart'),[{values:beta.upper,color:COLORS.upper,width:2},{values:beta.lower,color:COLORS.lower,width:2},{values:beta.prices,color:COLORS.current,width:3}]);
    const old=d.old;renderActions($('oldActions'),old.signal.lines);$('oldStatus').textContent=`${old.signal.name} (${old.gap_pct>=0?'+':''}${old.gap_pct.toFixed(2)}%)`;$('tqqqPrice').textContent=money(old.current_price);$('tqqqSma').textContent=money(old.sma_200);drawLineChart($('oldChart'),[{values:old.sma,color:COLORS.ma,width:2.5},{values:old.prices,color:COLORS.current,width:3}]);
    const f=d.fgi;$('fgiValue').textContent=Math.round(f.current);$('fgiValue').style.color=fgiColor(f.current);$('fgiRating').textContent=f.rating_ko;$('fgiRating').style.color=fgiColor(f.current);$('fgiNow').textContent=`현재 ${Math.round(f.current)}`;$('fgiAvg').textContent=`30일 평균 ${Math.round(f.average_30)}`;$('fgiNow').style.color=fgiColor(f.current);$('fgiAvg').style.color=fgiColor(f.average_30);drawGauge($('gauge'),f.current);drawFgiChart($('fgiChart'),f.values);
    window.addEventListener('resize',()=>{drawLineChart($('betaChart'),[{values:beta.upper,color:COLORS.upper,width:2},{values:beta.lower,color:COLORS.lower,width:2},{values:beta.prices,color:COLORS.current,width:3}]);drawLineChart($('oldChart'),[{values:old.sma,color:COLORS.ma,width:2.5},{values:old.prices,color:COLORS.current,width:3}]);drawGauge($('gauge'),f.current);drawFgiChart($('fgiChart'),f.values);},{passive:true});
  }catch(e){document.querySelector('.grid').innerHTML=`<article class="card card-wide error">데이터를 불러오지 못했습니다.<br>${e.message}</article>`;}
}
load();
