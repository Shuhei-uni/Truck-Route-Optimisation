// app.js
lucide.createIcons();

// Global State
let locations, demand, master, shifts, kpis;
let staticMap, animMap;
let demandLayer, routesLayer;
let animBgLayer;
let depotLoc;
let ganttChartObj = null;

let animInterval;
let animTime = 8 * 3600;
let isPlaying = false;
let truckMarkers = {};

const TIME_STEP = 30;
const FPS = 30;

const MAP_THEME = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
const MAP_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
const mapCenter = [-36.85, 174.75];

const timeDisplay = document.getElementById('time-display');
const timeSlider = document.getElementById('time-slider');
const btnPlay = document.getElementById('btn-anim-play');
const btnPause = document.getElementById('btn-anim-pause');

// ==========================================
// 1. Navigation & Views Logic
// ==========================================
const navButtons = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view');

navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        navButtons.forEach(b => b.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        
        btn.classList.add('active');
        const viewId = `view-${btn.dataset.view}`;
        document.getElementById(viewId).classList.add('active');
        
        setTimeout(() => {
            if(staticMap) staticMap.invalidateSize();
            if(animMap) animMap.invalidateSize();
        }, 100);
    });
});

// Setup static map once
staticMap = L.map('static-map').setView(mapCenter, 11);
L.tileLayer(MAP_THEME, { attribution: MAP_ATTR }).addTo(staticMap);

animMap = L.map('anim-map').setView(mapCenter, 11);
L.tileLayer(MAP_THEME, { attribution: MAP_ATTR }).addTo(animMap);
animBgLayer = L.layerGroup().addTo(animMap);

const btnDemand = document.getElementById('btn-show-demand');
const btnRoutes = document.getElementById('btn-show-routes');

btnDemand.addEventListener('click', () => {
    btnDemand.classList.add('active');
    btnRoutes.classList.remove('active');
    if (demandLayer) staticMap.addLayer(demandLayer);
    if (routesLayer) staticMap.removeLayer(routesLayer);
});

btnRoutes.addEventListener('click', () => {
    btnRoutes.classList.add('active');
    btnDemand.classList.remove('active');
    if (routesLayer) staticMap.addLayer(routesLayer);
    if (demandLayer) staticMap.removeLayer(demandLayer);
});

// ==========================================
// Main Dashboard Refresh Function
// ==========================================
window.refreshDashboard = function(data) {
    locations = data.locations;
    demand = data.demand;
    master = data.master;
    shifts = data.shifts;
    kpis = data.kpis || {};
    
    depotLoc = locations['Distribution Centre Auckland'];
    
    // 1. Update KPIs
    if(kpis.fleet_size) {
        document.getElementById('kpi-fleet-size').innerHTML = `${kpis.fleet_size} <span class="kpi-sub">trucks</span>`;
        const costM = (kpis.total_annual_cost / 1000000).toFixed(2);
        document.getElementById('kpi-annual-cost').innerHTML = `$${costM}M <span class="kpi-sub">/ yr</span>`;
        document.getElementById('kpi-stores').innerHTML = `${kpis.stores_covered} <span class="kpi-sub">stores</span>`;
    }
    
    // 2. Render Gantt
    renderGantt();

    // 2.5 Render Simulation Summary Table if present
    const sumTbody = document.querySelector('#simSummaryTable tbody');
    if(sumTbody) {
        sumTbody.innerHTML = '';
        if(kpis.sim_summary && kpis.sim_summary.length > 0) {
            kpis.sim_summary.forEach(row => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid #21262d';
                tr.innerHTML = `
                    <td style="padding: 10px;">${row.metric}</td>
                    <td style="padding: 10px; text-align: right; font-family: monospace; color: #79c0ff;">${row.value}</td>
                `;
                sumTbody.appendChild(tr);
            });
        }
    }
    
    // 3. Render Static Maps
    if (demandLayer) staticMap.removeLayer(demandLayer);
    if (routesLayer) staticMap.removeLayer(routesLayer);
    demandLayer = L.layerGroup();
    routesLayer = L.layerGroup();
    
    L.circleMarker([depotLoc.lat, depotLoc.lng], { radius: 8, color: '#e94560', fillOpacity: 1 })
      .bindPopup('<b>DEPOT</b>').addTo(staticMap);

    Object.keys(demand).forEach(store => {
        if(!locations[store]) return;
        const qty = demand[store];
        L.circleMarker([locations[store].lat, locations[store].lng], {
            radius: qty * 1.5,
            color: '#388bfd', fillColor: '#388bfd', fillOpacity: 0.6, weight: 1
        }).bindPopup(`<b>${store}</b><br>Mean Demand: ${qty.toFixed(1)} pallets`)
          .addTo(demandLayer);
    });

    master.forEach((route, idx) => {
        const latlngs = route.stores.filter(s => locations[s]).map(s => [locations[s].lat, locations[s].lng]);
        if(latlngs.length < 2) return;
        L.polyline(latlngs, {
            color: route.color,
            weight: route.assigned_to === 'WW' ? 3 : 2,
            opacity: 0.8,
            dashArray: route.assigned_to === 'WW' ? null : '5, 5'
        }).bindPopup(`<b>${route.assigned_to} Route ${idx+1}</b><br>Stores: ${route.stores.length-1}<br>Demand: ${route.demand} pal`)
          .addTo(routesLayer);
    });

    if (btnDemand.classList.contains('active')) {
        demandLayer.addTo(staticMap);
    } else {
        routesLayer.addTo(staticMap);
    }
    
    // 4. Setup Animation Map
    setupAnimation();
};

function renderGantt() {
    if(ganttChartObj) {
        ganttChartObj.destroy();
    }
    document.getElementById('gantt-wrapper').innerHTML = ''; // clear canvas
    const ctx = document.createElement('canvas');
    document.getElementById('gantt-wrapper').appendChild(ctx);

    const labels = [];
    const data1 = []; 
    const data2 = []; 
    const trucks = [...new Set(shifts.map(s => s.truck_id))].sort((a,b)=>a-b);
    
    trucks.forEach(tid => {
        labels.push(`Truck ${tid}`);
        const s1 = shifts.find(s => s.truck_id === tid && s.shift === 1);
        const s2 = shifts.find(s => s.truck_id === tid && s.shift === 2);
        if(s1) data1.push([8, 8 + s1.duration_sec / 3600]); else data1.push(null);
        if(s2) data2.push([14, 14 + s2.duration_sec / 3600]); else data2.push(null);
    });

    ganttChartObj = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                { label: 'Shift 1 (8 AM)', data: data1, backgroundColor: '#388bfd', barPercentage: 0.6 },
                { label: 'Shift 2 (2 PM)', data: data2, backgroundColor: '#bc8cff', barPercentage: 0.6 }
            ]
        },
        options: {
            indexAxis: 'y', responsive: true, maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: '#e6edf3' } },
                tooltip: { callbacks: { label: (ctx) => {
                    if (!ctx.raw) return '';
                    const hrs = (ctx.raw[1] - ctx.raw[0]).toFixed(1);
                    return `${ctx.dataset.label}: ${hrs} hrs`;
                }}}
            },
            scales: {
                x: { min: 7, max: 20, grid: { color: '#30363d' }, ticks: { color: '#8b949e', callback: val => `${val}:00` } },
                y: { grid: { display: false }, ticks: { color: '#e6edf3' } }
            }
        }
    });
}

function setupAnimation() {
    animBgLayer.clearLayers();
    pauseAnim();
    Object.values(truckMarkers).forEach(tm => {
        if(tm.marker) animMap.removeLayer(tm.marker);
    });
    truckMarkers = {};
    
    master.forEach((route) => {
        const latlngs = route.stores.filter(s => locations[s]).map(s => [locations[s].lat, locations[s].lng]);
        L.polyline(latlngs, { color: '#30363d', weight: 2, opacity: 0.5 }).addTo(animBgLayer);
    });
    L.circleMarker([depotLoc.lat, depotLoc.lng], { radius: 6, color: '#e94560' }).addTo(animBgLayer);

    shifts.forEach(shift => {
        const tid = shift.truck_id;
        if(!truckMarkers[tid]) {
            const icon = L.divIcon({ html: `🚚`, className: 'truck-icon', iconSize: [24, 24], iconAnchor: [12, 12] });
            const marker = L.marker([depotLoc.lat, depotLoc.lng], { icon: icon, zIndexOffset: 1000 })
                .bindTooltip(`<b>Truck ${tid}</b>`).addTo(animMap);
            truckMarkers[tid] = { marker: marker, active: false };
        }
    });

    animTime = 8 * 3600;
    updateTruckPositions(animTime);
}

function formatTime(secs) {
    const h = Math.floor(secs / 3600);
    const m = Math.floor((secs % 3600) / 60);
    return `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}`;
}

function updateTruckPositions(t) {
    timeDisplay.innerText = formatTime(t);
    timeSlider.value = t;

    Object.values(truckMarkers).forEach(tm => {
        tm.marker.setOpacity(0);
        tm.active = false;
    });

    shifts.forEach(shift => {
        if(t >= shift.start_time && t <= shift.end_time) {
            const tm = truckMarkers[shift.truck_id];
            tm.active = true;
            tm.marker.setOpacity(1);

            const p = (t - shift.start_time) / shift.duration_sec;
            const coords = shift.stores.filter(s => locations[s]).map(s => locations[s]);
            if(coords.length < 2) return;
            
            const numSegments = coords.length - 1;
            let segmentIdx = Math.floor(p * numSegments);
            if(segmentIdx >= numSegments) segmentIdx = numSegments - 1;
            
            const segmentP = (p * numSegments) - segmentIdx;
            const startLoc = coords[segmentIdx];
            const endLoc = coords[segmentIdx + 1];
            
            const currentLat = startLoc.lat + (endLoc.lat - startLoc.lat) * segmentP;
            const currentLng = startLoc.lng + (endLoc.lng - startLoc.lng) * segmentP;
            
            tm.marker.setLatLng([currentLat, currentLng]);
            
            const el = tm.marker.getElement();
            if(el) {
                const bounce = 1 + Math.sin(t / 100) * 0.1;
                el.style.transform += ` scale(${bounce})`;
            }
        }
    });
}

function tickAnimation() {
    if(!isPlaying) return;
    animTime += TIME_STEP * 4;
    if(animTime >= 21 * 3600) {
        animTime = 8 * 3600;
        pauseAnim();
    }
    updateTruckPositions(animTime);
}

function playAnim() {
    isPlaying = true;
    btnPlay.classList.add('primary');
    btnPause.classList.remove('active');
    clearInterval(animInterval);
    animInterval = setInterval(tickAnimation, 1000 / FPS);
}

function pauseAnim() {
    isPlaying = false;
    btnPause.classList.add('active');
    btnPlay.classList.remove('primary');
    clearInterval(animInterval);
}

btnPlay.addEventListener('click', playAnim);
btnPause.addEventListener('click', pauseAnim);

// Initialize with data loaded from script tag
if (typeof REPORT_DATA !== 'undefined') {
    window.refreshDashboard(REPORT_DATA);
}
