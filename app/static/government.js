const $ = id => document.getElementById(id);
let map = L.map('map', {zoomControl:false}).setView([13.0827, 80.2707], 11), markers = new Map(), defectMarkers = new Map(), accidentMarkers = new Map(), trafficRoadLayer = L.layerGroup(), active = null, alertedAccidentId = null;
L.control.zoom({position:'topleft'}).addTo(map);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19, attribution:'© OpenStreetMap contributors'}).addTo(map);
trafficRoadLayer.addTo(map);
const trafficLegend = L.control({position:'bottomright'});
trafficLegend.onAdd = () => { const panel = L.DomUtil.create('div', 'traffic-map-legend'); panel.innerHTML = '<b>LIVE TRAFFIC DENSITY</b><span><i class="high"></i>High - heavy traffic</span><span><i class="moderate"></i>Moderate traffic</span><span><i class="low"></i>Low - clear traffic</span>'; return panel; };
trafficLegend.addTo(map);

function escapeHtml(value) { const element = document.createElement('div'); element.textContent = value ?? ''; return element.innerHTML; }
function formatLocation(defect) { return `${Number(defect.latitude).toFixed(5)}, ${Number(defect.longitude).toFixed(5)}`; }
function formatDate(value) { return value ? new Date(value).toLocaleDateString() : 'Not set'; }
function setClock() { $('clock').textContent = new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}); }
setClock(); setInterval(setClock, 1000);

$('findButton').addEventListener('click', () => { const value = $('routeSearch').value.trim().toLowerCase(); if (value) { active = value; refresh(); } });
$('defectToggle').addEventListener('click', () => { $('defectPanel').hidden = !$('defectPanel').hidden; });
$('closeDefects').addEventListener('click', () => { $('defectPanel').hidden = true; });
$('trafficToggle').addEventListener('click', () => { $('trafficPanel').hidden = !$('trafficPanel').hidden; });
$('closeTraffic').addEventListener('click', () => { $('trafficPanel').hidden = true; });
$('accidentToggle').addEventListener('click', () => { $('accidentPanel').hidden = !$('accidentPanel').hidden; });
$('closeAccidents').addEventListener('click', () => { $('accidentPanel').hidden = true; });
$('dismissAccidentAlert').addEventListener('click', () => { $('highAccidentAlert').hidden = true; });
$('allBusesToggle').addEventListener('click', () => { $('allBusesPanel').hidden = !$('allBusesPanel').hidden; $('addBusPanel').hidden = true; refreshBuses(); });
$('closeAllBuses').addEventListener('click', () => { $('allBusesPanel').hidden = true; });
$('addBusToggle').addEventListener('click', () => { $('addBusPanel').hidden = !$('addBusPanel').hidden; $('allBusesPanel').hidden = true; });
$('closeAddBus').addEventListener('click', () => { $('addBusPanel').hidden = true; });
$('addBusForm').addEventListener('submit', saveBus);
$('defectRows').addEventListener('change', event => { if (event.target.matches('select[data-id]')) saveDefect(event.target.dataset.id, {status:event.target.value}); });
$('defectRows').addEventListener('change', event => { if (event.target.matches('input[data-id]')) saveDefect(event.target.dataset.id, {deadline:event.target.value || null}); });

async function saveDefect(id, changes) {
  try {
    const response = await fetch(`/api/infrastructure-defects/${id}`, {method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify(changes)});
    if (!response.ok) throw new Error((await response.json()).detail || 'Update failed');
    refreshDefects();
  } catch (error) { console.error(error); alert(`Could not save defect update: ${error.message}`); }
}

async function refresh() {
  try {
    const [fleetResponse, analyticsResponse] = await Promise.all([fetch('/api/vehicles'), fetch('/api/analytics')]);
    renderFleet(await fleetResponse.json(), await analyticsResponse.json());
  } catch (error) { console.error(error); }
  refreshDefects(); refreshTraffic(); refreshAccidents(); refreshBuses(); setTimeout(refresh, 3000);
}

async function refreshBuses() {
  try { renderBuses(await (await fetch('/api/buses')).json()); } catch (error) { console.error(error); }
}

function busLocation(bus) {
  const latitude = bus.online ? bus.live_latitude : bus.latitude;
  const longitude = bus.online ? bus.live_longitude : bus.longitude;
  return latitude == null || longitude == null ? 'Not set' : `${Number(latitude).toFixed(5)}, ${Number(longitude).toFixed(5)}`;
}

function renderBuses(buses) {
  $('allBusesRows').innerHTML = buses.length ? buses.map(bus => {
    const route = `${escapeHtml(bus.source)} → ${escapeHtml(bus.destination)}`;
    const name = bus.online
      ? `<button class="fleet-bus-link" data-bus="${escapeHtml(bus.bus_number)}" data-lat="${bus.live_latitude ?? bus.latitude ?? ''}" data-lng="${bus.live_longitude ?? bus.longitude ?? ''}">🚌 ${escapeHtml(bus.bus_number)}</button>`
      : `<b class="offline-bus">🚌 ${escapeHtml(bus.bus_number)}</b>`;
    const connection = bus.online ? `<b class="online-status">● ONLINE</b><small>${bus.last_seen ? new Date(bus.last_seen).toLocaleTimeString() : 'camera active'}</small>` : '<b class="offline-status">● OFFLINE</b><small>Camera not active</small>';
    const live = bus.online ? `<b>${bus.object_count} objects</b><small>${escapeHtml(bus.density)} density · ${bus.vehicle_count} vehicles</small>` : '<span class="muted">No live data</span>';
    const accident = bus.online ? `<b class="${bus.latest_accident_id ? 'accident-detected' : 'accident-clear'}">${escapeHtml(bus.accident_status)}</b>` : '<span class="muted">Offline</span>';
    return `<tr><td>${name}</td><td>${route}</td><td>${busLocation(bus)}</td><td>${connection}</td><td>${live}</td><td>${accident}</td></tr>`;
  }).join('') : '<tr><td colspan="6" class="muted">No buses in the registry. Use Add bus to create the first entry.</td></tr>';
  document.querySelectorAll('.fleet-bus-link').forEach(button => button.addEventListener('click', () => {
    active = button.dataset.bus.toLowerCase(); $('routeSearch').value = button.dataset.bus; $('allBusesPanel').hidden = true;
    if (button.dataset.lat && button.dataset.lng) map.setView([Number(button.dataset.lat), Number(button.dataset.lng)], 16);
    refresh();
  }));
}

async function saveBus(event) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const payload = Object.fromEntries(form.entries());
  payload.latitude = payload.latitude === '' ? null : Number(payload.latitude);
  payload.longitude = payload.longitude === '' ? null : Number(payload.longitude);
  $('addBusMessage').textContent = 'Saving…';
  try {
    const response = await fetch('/api/buses', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || 'Could not save this bus');
    $('addBusMessage').textContent = `Saved ${body.bus_number}.`;
    event.currentTarget.reset();
    refreshBuses();
  } catch (error) { $('addBusMessage').textContent = error.message; }
}

async function refreshDefects() {
  try { renderDefects(await (await fetch('/api/infrastructure-defects')).json()); } catch (error) { console.error(error); }
}

async function refreshTraffic() {
  try { renderTraffic(await (await fetch('/api/traffic-analysis')).json()); } catch (error) { console.error(error); }
}

async function refreshAccidents() {
  try { renderAccidents(await (await fetch('/api/accidents')).json()); } catch (error) { console.error(error); }
}

function renderFleet(fleet, analytics) {
  $('delayCount').textContent = analytics.possible_delay_routes.length;
  $('vehicleObservations').textContent = analytics.vehicle_observations;
  $('pedestrianObservations').textContent = analytics.pedestrian_observations;
  const selected = fleet.find(item => active && item.driver_id.toLowerCase() === active) || fleet[0];
  if (selected) { active = selected.driver_id.toLowerCase(); $('routeSearch').value = selected.driver_id; renderSelected(selected); }
  else $('activeVehicle').innerHTML = '<div><b>🚌 No active vehicle</b><span>Waiting for driver location</span></div>';
  $('trafficStatus').textContent = analytics.possible_delay_routes.length ? 'POSSIBLE DELAY' : 'NORMAL / WAITING';
  $('trafficDetail').textContent = analytics.possible_delay_routes.length ? `High vehicle density: ${analytics.possible_delay_routes.join(', ')}.` : analytics.note;
  fleet.forEach(vehicle => {
    if (vehicle.latitude == null) return;
    const position = [vehicle.latitude, vehicle.longitude], popup = `<b>${escapeHtml(vehicle.driver_id)}</b><br>${vehicle.detections.length} objects • ${vehicle.analysis.density} density`;
    if (markers.has(vehicle.driver_id)) markers.get(vehicle.driver_id).setLatLng(position).setPopupContent(popup);
    else markers.set(vehicle.driver_id, L.marker(position).addTo(map).bindPopup(popup));
  });
}

function renderSelected(v) {
  const time = v.last_seen ? new Date(v.last_seen).toLocaleTimeString() : '–', analysis = v.analysis;
  $('activeVehicle').innerHTML = `<div><b>🚌 ${escapeHtml(v.driver_id)}</b><span class="green">● LIVE</span></div><div class="tracked-stats"><span>Status <b>Active</b></span><span>Scans <b>${v.scans}</b></span></div>`;
  $('overlayVehicle').textContent = v.driver_id; $('overlayObjects').textContent = v.detections.length; $('overlayUpdate').textContent = time;
  $('trafficStatus').textContent = analysis.vehicle_count >= 5 ? 'POSSIBLE DELAY' : 'NORMAL';
  $('trafficDetail').textContent = analysis.vehicle_count >= 5 ? 'High vehicle density in this camera scene. Confirm with speed or route data.' : 'No local high-density traffic signal.';
  $('analysisVehicle').textContent = `Vehicle ${v.driver_id}`; $('analysisScanStatus').textContent = v.last_seen ? 'LIVE' : 'WAITING';
  $('govDensity').textContent = analysis.density; $('govPedestrians').textContent = analysis.person_count; $('govVehicles').textContent = analysis.vehicle_count;
  $('govClassCount').textContent = `${v.detections.length} objects detected`;
  $('govAlerts').innerHTML = analysis.alerts.length ? analysis.alerts.map(alert => `<span class="alert ${alert.level}">${escapeHtml(alert.message)}</span>`).join('') : '<span class="good">✓ No pedestrian-density or traffic-density alert.</span>';
  $('govClasses').innerHTML = Object.entries(analysis.counts || {}).length ? Object.entries(analysis.counts).map(([label,count]) => `<span class="class-chip"><b>${escapeHtml(label)}</b> ${count}</span>`).join('') : '<span class="muted">No detections yet.</span>';
  if (v.latitude != null) map.setView([v.latitude, v.longitude], 14);
}

function renderDefects(data) {
  const {defects, counts, priority_queue: queue} = data;
  $('defectTotal').textContent = defects.length;
  $('detectedCount').textContent = counts.Detected || 0; $('progressCount').textContent = counts['In progress'] || 0; $('solvedCount').textContent = counts.Solved || 0;
  $('defectRows').innerHTML = defects.length ? defects.map(defect => `<tr><td><b>${escapeHtml(defect.defect_type)}</b><small>${Math.round(defect.confidence * 100)}% confidence · priority ${defect.priority}</small></td><td><button class="location-link" data-lat="${defect.latitude}" data-lng="${defect.longitude}">${formatLocation(defect)}</button><small>${escapeHtml(defect.driver_id)}</small></td><td><select data-id="${defect.id}"><option ${defect.status === 'Detected' ? 'selected' : ''}>Detected</option><option ${defect.status === 'In progress' ? 'selected' : ''}>In progress</option><option ${defect.status === 'Solved' ? 'selected' : ''}>Solved</option></select></td><td><input type="date" data-id="${defect.id}" value="${defect.deadline ? defect.deadline.slice(0,10) : ''}"><small>${formatDate(defect.deadline)}</small></td></tr>`).join('') : '<tr><td colspan="4" class="muted">No GPS-linked defects yet. Start GPS tracking on the driver panel, then run pothole detection.</td></tr>';
  $('priorityQueue').innerHTML = queue.length ? queue.map(defect => `<li><b>${defect.defect_type}</b><span>Priority ${defect.priority} · ${formatLocation(defect)}</span><small>${escapeHtml(defect.status)} · ${Math.round(defect.confidence * 100)}% confidence</small></li>`).join('') : '<li class="muted">No open defects yet.</li>';
  document.querySelectorAll('.location-link').forEach(button => button.addEventListener('click', () => { map.setView([Number(button.dataset.lat), Number(button.dataset.lng)], 17); if ($('defectPanel').hidden) $('defectPanel').hidden = false; }));
  const known = new Set(defects.map(defect => String(defect.id)));
  defectMarkers.forEach((marker, id) => { if (!known.has(id)) { map.removeLayer(marker); defectMarkers.delete(id); } });
  defects.forEach(defect => {
    const markerHtml = `<b>Pothole #${defect.id}</b><br>${formatLocation(defect)}<br>Priority ${defect.priority} · ${escapeHtml(defect.status)}`;
    if (defectMarkers.has(String(defect.id))) defectMarkers.get(String(defect.id)).setLatLng([defect.latitude, defect.longitude]).setPopupContent(markerHtml);
    else defectMarkers.set(String(defect.id), L.circleMarker([defect.latitude, defect.longitude], {radius:8, color:'#d61f45', fillColor:'#ef476f', fillOpacity:.9}).addTo(map).bindPopup(markerHtml));
  });
}

function renderTraffic(data) {
  const {events, priority_queue: queue, route_patterns: patterns = [], forecasts = [], method_note: methodNote = ''} = data;
  $('trafficTotal').textContent = events.length;
  $('trafficRows').innerHTML = events.length ? events.map(event => `<tr><td><b>🚗 ${event.cars} · 🏍️ ${event.bikes} · 🚌 ${event.buses}</b><small>Total vehicle count: ${event.total_vehicles}</small></td><td><button class="traffic-location-link location-link" data-lat="${event.latitude}" data-lng="${event.longitude}">${formatLocation(event)}</button><small>${escapeHtml(event.driver_id)}</small></td><td><b>${escapeHtml(event.density)}</b><small>Estimated local delay: ~${event.estimated_delay_minutes} min</small><small>${escapeHtml(event.insight)}</small></td></tr>`).join('') : '<tr><td colspan="3" class="muted">No GPS-linked traffic observations yet. Start GPS tracking and run live object detection.</td></tr>';
  $('trafficPriorityQueue').innerHTML = queue.length ? queue.map(event => `<li><b>🚗 ${event.cars} · 🏍️ ${event.bikes} · 🚌 ${event.buses} — ${escapeHtml(event.density)}</b><span>Priority ${event.priority} · ${formatLocation(event)}</span><small>~${event.estimated_delay_minutes} min local delay · ${escapeHtml(event.insight)}</small></li>`).join('') : '<li class="muted">No high-density traffic observations yet.</li>';
  $('trafficMethodNote').textContent = methodNote;
  $('routePatterns').innerHTML = patterns.length ? patterns.map(pattern => `<li><b>${escapeHtml(pattern.driver_id)} — ${escapeHtml(pattern.density)} density</b><span>Origin ${Number(pattern.origin.latitude).toFixed(4)}, ${Number(pattern.origin.longitude).toFixed(4)} → latest ${Number(pattern.latest_location.latitude).toFixed(4)}, ${Number(pattern.latest_location.longitude).toFixed(4)}</span><small>${pattern.samples} samples · avg ${pattern.average_vehicles} vehicles · estimated local delay up to ${pattern.estimated_delay_minutes} min</small></li>`).join('') : '<li class="muted">No route samples yet.</li>';
  const forecastCell = projection => `<b class="forecast-${projection.density.toLowerCase()}">${escapeHtml(projection.density)}</b><small>~${projection.estimated_vehicles} vehicles</small><small>~${projection.estimated_delay_minutes} min local delay</small>`;
  $('forecastRows').innerHTML = forecasts.length ? forecasts.map(forecast => `<tr><td><b>🚌 ${escapeHtml(forecast.driver_id)}</b><small>${escapeHtml(forecast.source)} → ${escapeHtml(forecast.destination)}</small><small>${forecast.samples} samples · ${escapeHtml(forecast.confidence)} confidence</small></td><td><b>${escapeHtml(forecast.trend)}</b><small>Camera-count trend</small></td><td>${forecastCell(forecast.projections[0])}</td><td>${forecastCell(forecast.projections[1])}</td><td>${forecastCell(forecast.projections[2])}</td></tr>`).join('') : '<tr><td colspan="5" class="muted">Waiting for GPS-linked vehicle observations. Start driver GPS and live camera detection.</td></tr>';
  renderTrafficRoadOverlay(events);
  document.querySelectorAll('.traffic-location-link').forEach(button => button.addEventListener('click', () => { map.setView([Number(button.dataset.lat), Number(button.dataset.lng)], 17); if ($('trafficPanel').hidden) $('trafficPanel').hidden = false; }));
}

function densityStyle(density) {
  if (density === 'High') return {color:'#dc2626', label:'HIGH - heavy traffic'};
  if (density === 'Moderate') return {color:'#f59e0b', label:'MODERATE traffic'};
  return {color:'#16a34a', label:'LOW - clear traffic'};
}

function renderTrafficRoadOverlay(events) {
  trafficRoadLayer.clearLayers();
  // A point indicates the latest density observation. We intentionally do not draw route lines.
  const latest = new Map();
  events.forEach(event => latest.set(event.driver_id, event));
  latest.forEach(event => {
    const style = densityStyle(event.density), current = [Number(event.latitude), Number(event.longitude)];
    L.circleMarker(current, {radius:10, color:style.color, fillColor:style.color, fillOpacity:.5, weight:5}).bindTooltip(`${style.label}: ${event.total_vehicles} vehicles`).addTo(trafficRoadLayer);
  });
}

function renderAccidents(data) {
  const incidents = data.incidents || [];
  $('accidentTotal').textContent = incidents.length;
  $('accidentRows').innerHTML = incidents.length ? incidents.map(item => { const plate = (item.plates || []).map(p => `${Math.round(p.confidence * 100)}%`).join(', ') || 'None'; const crop = (item.plates || []).find(p => p.crop_url); return `<tr><td><b class="severity-${item.severity.toLowerCase()}">${escapeHtml(item.severity)}</b><small>${Math.round(item.confidence * 100)}% confidence</small></td><td><button class="accident-location-link location-link" data-lat="${item.latitude}" data-lng="${item.longitude}">${formatLocation(item)}</button><small>${escapeHtml(item.driver_id)}</small></td><td><small>${escapeHtml(plate)} plate</small>${crop ? `<a class="evidence-link" target="_blank" href="${crop.crop_url}">Crop</a>` : ''}${item.evidence_path ? `<a class="evidence-link" target="_blank" href="${item.evidence_path}">Evidence</a>` : ''}</td><td><a class="report-link" target="_blank" href="/api/accidents/${item.id}/report.pdf">Generate<br>PDF</a></td></tr>`; }).join('') : '<tr><td colspan="4" class="muted">No GPS-linked accidents yet.</td></tr>';
  document.querySelectorAll('.accident-location-link').forEach(button => button.addEventListener('click', () => map.setView([Number(button.dataset.lat), Number(button.dataset.lng)], 17)));
  incidents.forEach(item => { const popup = `<b>🚨 ${escapeHtml(item.severity)} accident</b><br>${formatLocation(item)}<br>Confidence ${Math.round(item.confidence * 100)}%`; if (accidentMarkers.has(String(item.id))) accidentMarkers.get(String(item.id)).setLatLng([item.latitude, item.longitude]).setPopupContent(popup); else accidentMarkers.set(String(item.id), L.marker([item.latitude, item.longitude], {icon:L.divIcon({className:'accident-map-icon', html:'🚨', iconSize:[30,30]})}).addTo(map).bindPopup(popup)); });
  // Every saved accident is operationally relevant. Show it once per incident, not only when its AI severity is High.
  const latest = incidents[0];
  if (latest && alertedAccidentId !== latest.id) {
    alertedAccidentId = latest.id;
    $('highAccidentText').textContent = `Alert! → Bus no: ${latest.driver_id} detected an accident (${latest.severity} severity, ${Math.round(latest.confidence * 100)}% confidence) at ${formatLocation(latest)}.`;
    $('highAccidentAlert').hidden = false;
  }
}

refresh();
