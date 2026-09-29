let scenario = null;
let plan = null;
const colors = ["#00e0b8", "#ff0053", "#ffd166", "#8a83d1", "#00a6ff", "#22c55e"];

async function loadDemo() {
  const res = await fetch('/static/demo_scenario.json').catch(() => null);
  if (res && res.ok) return await res.json();
  return DEMO_SCENARIO;
}

function deepClone(x) { return JSON.parse(JSON.stringify(x)); }
function coordsFromScenario(s) {
  const arr = [];
  const addPoly = g => g?.coordinates?.forEach(r => r.forEach(c => arr.push(c)));
  addPoly(s.survey_area); addPoly(s.allowed_airspace); (s.no_fly_zones || []).forEach(addPoly);
  (s.launch_points || []).forEach(p => arr.push(p.coord)); (s.reserve_points || []).forEach(p => arr.push(p.coord));
  if (plan) plan.missions.forEach(m => m.route.forEach(p => arr.push([p.lon, p.lat])));
  return arr;
}
function projectFactory(s) {
  const coords = coordsFromScenario(s);
  const minLon = Math.min(...coords.map(c => c[0])), maxLon = Math.max(...coords.map(c => c[0]));
  const minLat = Math.min(...coords.map(c => c[1])), maxLat = Math.max(...coords.map(c => c[1]));
  const canvas = document.getElementById('mapCanvas');
  const w = canvas.clientWidth, h = canvas.clientHeight;
  canvas.width = w * devicePixelRatio; canvas.height = h * devicePixelRatio;
  const pad = 58;
  const sx = (w - pad * 2) / Math.max(0.00001, maxLon - minLon);
  const sy = (h - pad * 2) / Math.max(0.00001, maxLat - minLat);
  const scale = Math.min(sx, sy);
  return c => [pad + (c[0] - minLon) * scale, h - pad - (c[1] - minLat) * scale];
}
function drawPolygon(ctx, project, rings, fill, stroke, width = 2) {
  ctx.beginPath();
  rings.forEach((ring, ri) => ring.forEach((c, i) => {
    const [x,y] = project(c); if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
  }));
  ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.strokeStyle = stroke; ctx.lineWidth = width; ctx.stroke();
}
function draw() {
  if (!scenario) return;
  const canvas = document.getElementById('mapCanvas');
  const ctx = canvas.getContext('2d');
  const project = projectFactory(scenario);
  ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
  ctx.clearRect(0,0,canvas.clientWidth, canvas.clientHeight);
  ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  drawPolygon(ctx, project, scenario.allowed_airspace.coordinates, 'rgba(0,224,184,.05)', 'rgba(0,224,184,.35)', 2);
  drawPolygon(ctx, project, scenario.survey_area.coordinates, 'rgba(138,131,209,.15)', 'rgba(138,131,209,.85)', 3);
  (scenario.no_fly_zones || []).forEach(z => drawPolygon(ctx, project, z.coordinates, 'rgba(255,0,83,.25)', 'rgba(255,0,83,.9)', 2));
  function drawPoint(p, color, label) {
    const [x,y] = project(p.coord); ctx.fillStyle = color; ctx.beginPath(); ctx.arc(x,y,7,0,Math.PI*2); ctx.fill();
    ctx.fillStyle = '#f6f7ff'; ctx.font = '12px Inter, sans-serif'; ctx.fillText(label, x+10, y-8);
  }
  scenario.launch_points.forEach(p => drawPoint(p, '#00e0b8', p.name));
  (scenario.reserve_points || []).forEach(p => drawPoint(p, '#ffd166', p.name));
  if (plan) {
    plan.missions.forEach((m, idx) => {
      ctx.strokeStyle = colors[idx % colors.length]; ctx.lineWidth = 4;
      ctx.beginPath();
      m.route.forEach((p, i) => { const [x,y] = project([p.lon, p.lat]); if (i === 0) ctx.moveTo(x,y); else ctx.lineTo(x,y); });
      ctx.stroke();
    });
  }
}
async function runPlan() {
  try {
    const s = JSON.parse(document.getElementById('jsonInput').value);
    s.optimization = document.getElementById('optimization').value;
    s.survey_type = document.getElementById('surveyType').value;
    s.wind_speed_mps = Number(document.getElementById('wind').value);
    scenario = s;
    const res = await fetch('/api/plan', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(s) });
    if (!res.ok) throw new Error(await res.text());
    plan = await res.json();
    renderResults(); draw();
  } catch (e) { alert('Ошибка планирования: ' + e.message); }
}
function renderResults() {
  const s = plan.summary;
  document.getElementById('results').innerHTML = `
    <div class="metric"><b>${s.feasible ? 'Да' : 'Нет'}</b><span>Выполнимо</span></div>
    <div class="metric"><b>${s.makespan_min}</b><span>мин до завершения</span></div>
    <div class="metric"><b>${s.total_airtime_min}</b><span>суммарный налет, мин</span></div>
    <div class="metric"><b>${s.active_drones}</b><span>активных БВС</span></div>`;
  document.getElementById('missions').innerHTML = plan.missions.map((m,i) => `
    <div class="card"><div><b style="color:${colors[i%colors.length]}">${m.drone_id} · ${m.model}</b>
      <small>${m.launch_point} → ${m.landing_point}; ${m.assigned_strips} галсов</small>
      <small>${m.distance_m} м · ${m.airtime_min} мин · ${m.status}</small></div><div>${Math.round(m.survey_length_m)} м съемки</div></div>`).join('') +
      (s.warnings?.length ? `<div class="warning">${s.warnings.join('<br>')}</div>` : '');
}
async function download(kind) {
  if (!plan) return alert('Сначала постройте план');
  const endpoint = kind === 'kml' ? '/api/export/kml' : '/api/export/geojson';
  const res = await fetch(endpoint, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(plan) });
  const blob = await res.blob();
  const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = kind === 'kml' ? 'mission.kml' : 'mission.geojson'; a.click();
}
window.addEventListener('resize', draw);
window.addEventListener('DOMContentLoaded', async () => {
  scenario = await loadDemo();
  document.getElementById('jsonInput').value = JSON.stringify(scenario, null, 2);
  document.getElementById('optimization').value = scenario.optimization;
  document.getElementById('surveyType').value = scenario.survey_type;
  document.getElementById('wind').value = scenario.wind_speed_mps;
  draw();
});

const DEMO_SCENARIO = {"name":"Demo","survey_type":"RGB","optimization":"balanced","wind_speed_mps":6,"wind_direction_deg":245,"max_work_time_min":55,"max_drones":4,"launch_points":[{"id":"lp-1","name":"ВПП Север","coord":[37.6178,55.7605],"type":"launch"},{"id":"lp-2","name":"ВПП Юг","coord":[37.6285,55.7487],"type":"launch"}],"reserve_points":[{"id":"rp-1","name":"Резерв 1","coord":[37.6126,55.752],"type":"reserve"},{"id":"rp-2","name":"Резерв 2","coord":[37.6369,55.7567],"type":"reserve"}],"fleet":[{"id":"g201","model":"Геоскан 201","count":2,"speed_mps":16,"endurance_min":45,"max_altitude_m":150,"battery_wh":520,"payloads":["RGB","multispectral"]},{"id":"g801","model":"Геоскан 801","count":1,"speed_mps":22,"endurance_min":120,"max_altitude_m":150,"battery_wh":2100,"payloads":["RGB","LiDAR","geophysical"]},{"id":"gemini","model":"Геоскан Gemini","count":1,"speed_mps":12,"endurance_min":35,"max_altitude_m":120,"battery_wh":360,"payloads":["RGB","IR"]}],"survey_area":{"type":"Polygon","coordinates":[[[37.6068,55.7479],[37.6417,55.7486],[37.6412,55.7644],[37.6074,55.7649],[37.6068,55.7479]]]},"allowed_airspace":{"type":"Polygon","coordinates":[[[37.6043,55.7461],[37.6445,55.7464],[37.6446,55.7661],[37.6046,55.7664],[37.6043,55.7461]]]},"no_fly_zones":[{"type":"Polygon","coordinates":[[[37.621,55.7522],[37.6288,55.7525],[37.6284,55.7577],[37.6207,55.7574],[37.621,55.7522]]]},{"type":"Polygon","coordinates":[[[37.6333,55.7592],[37.6383,55.7593],[37.6381,55.7624],[37.633,55.7622],[37.6333,55.7592]]]}]};
