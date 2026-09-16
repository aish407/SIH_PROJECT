const $ = (id) => document.getElementById(id);
const video = $('sourceVideo'), frame = $('annotatedFrame'), canvas = $('captureCanvas');
const ctx = canvas.getContext('2d');
let stream = null, running = false, inFlight = false, map, markers = new Map();

document.querySelectorAll('.tab').forEach(button => button.addEventListener('click', () => {
  document.querySelectorAll('.tab,.panel').forEach(x => x.classList.remove('active'));
  button.classList.add('active'); $(button.dataset.panel).classList.add('active');
  if (button.dataset.panel === 'government') setTimeout(() => map.invalidateSize(), 100);
}));

$('confidence').addEventListener('input', e => $('confidenceValue').textContent = `${e.target.value}%`);
$('videoFile').addEventListener('change', event => {
  const file = event.target.files[0]; if (!file) return;
  stop(); video.srcObject = null; video.src = URL.createObjectURL(file); video.loop = true;
  video.onloadedmetadata = () => { video.play(); start(); };
});
$('cameraButton').addEventListener('click', async () => {
  try { stop(); stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false }); video.src = ''; video.srcObject = stream; await video.play(); start(); }
  catch (err) { setStatus(`Camera unavailable: ${err.message}`); }
});
$('stopButton').addEventListener('click', stop);

function driverId(){ return $('driverId').value.trim() || 'Unidentified driver'; }
function setStatus(text){ $('feedStatus').textContent = text; }
function start(){ running = true; $('stopButton').disabled = false; setStatus('Detecting'); detectLoop(); }
function stop(){ running = false; $('stopButton').disabled = true; if(stream){stream.getTracks().forEach(t=>t.stop());stream=null;} setStatus('Stopped'); }
async function detectLoop(){
  if (!running) return;
  if (!inFlight && video.readyState >= 2) {
    inFlight = true; canvas.width = video.videoWidth; canvas.height = video.videoHeight; ctx.drawImage(video, 0, 0);
    canvas.toBlob(async blob => { try { await sendFrame(blob); } catch (e) { setStatus('Detection failed'); console.error(e); } finally { inFlight = false; } }, 'image/jpeg', .86);
  }
  setTimeout(detectLoop, 550);
}
async function sendFrame(blob){
  const data = new FormData(); data.append('image', blob, 'frame.jpg'); data.append('driver_id', driverId()); data.append('confidence', Number($('confidence').value)/100);
  const response = await fetch('/api/detect', {method:'POST', body:data}); if(!response.ok) throw new Error(await response.text());
  const result = await response.json(); frame.src = result.image; $('emptyFeed').style.display = 'none'; setStatus(`${result.count} objects detected`); renderDetections(result.detections, result.count);
}
function renderDetections(items, count){ $('metric').innerHTML = `<b>${count}</b><span>objects in latest frame</span>`; $('detections').innerHTML = items.length ? items.map(d=>`<div class="detection"><span>${escapeHtml(d.class)}</span><span class="badge">${Math.round(d.confidence*100)}%</span></div>`).join('') : '<p>No objects above the selected confidence.</p>'; }
function escapeHtml(value){ const node=document.createElement('div');node.textContent=value;return node.innerHTML; }

$('locationButton').addEventListener('click', () => {
  if (!navigator.geolocation) return $('locationStatus').textContent = 'Geolocation is unsupported';
  $('locationStatus').textContent = 'Requesting location…';
  navigator.geolocation.getCurrentPosition(sendLocation, error => $('locationStatus').textContent = `Location error: ${error.message}`, {enableHighAccuracy:true, timeout:12000, maximumAge:10000});
});
async function sendLocation(position){
  const body = {driver_id:driverId(), latitude:position.coords.latitude, longitude:position.coords.longitude, accuracy_m:position.coords.accuracy};
  const response = await fetch('/api/location',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  $('locationStatus').textContent = response.ok ? `Location shared (±${Math.round(body.accuracy_m)}m)` : 'Location update failed';
}

map = L.map('map').setView([20.5937, 78.9629], 5);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap contributors'}).addTo(map);
async function refreshFleet(){
  try { const response = await fetch('/api/vehicles'); const vehicles = await response.json(); renderFleet(vehicles); }
  catch(error){ console.error(error); }
  setTimeout(refreshFleet, 2000);
}
function renderFleet(vehicles){
  $('fleetCount').textContent = `${vehicles.length} online`;
  $('fleetList').innerHTML = vehicles.length ? vehicles.map(v => {
    const label = v.detections?.length ? v.detections.map(d=>d.class).join(', ') : 'No recent detections';
    return `<div class="fleet-item"><h4>${escapeHtml(v.driver_id)}</h4><small>${escapeHtml(label)}</small><small>${v.latitude == null ? 'Location unavailable' : `${v.latitude.toFixed(5)}, ${v.longitude.toFixed(5)}`}</small>${v.last_frame ? `<img class="fleet-image" src="${v.last_frame}" alt="Latest annotated frame">` : ''}</div>`;
  }).join('') : '<p>No drivers have reported yet.</p>';
  vehicles.forEach(v => { if(v.latitude == null) return; const pos=[v.latitude,v.longitude]; const text=`<b>${escapeHtml(v.driver_id)}</b><br>${v.detections?.length||0} objects in latest frame`; if(markers.has(v.driver_id)){markers.get(v.driver_id).setLatLng(pos).setPopupContent(text);}else{markers.set(v.driver_id,L.marker(pos).addTo(map).bindPopup(text));} });
}
refreshFleet();
