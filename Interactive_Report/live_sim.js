// live_sim.js

document.addEventListener('DOMContentLoaded', () => {
    // 1. Setup UI Values
    const els = {
        fleetSize: document.getElementById('fleetSize'),
        truckCost: document.getElementById('truckCost'),
        mfCost: document.getElementById('mfCost'),
        otRate: document.getElementById('otRate'),
        penalty: document.getElementById('penalty'),
        demandMean: document.getElementById('demandMean'),
        demandStd: document.getElementById('demandStd'),
    };

    Object.keys(els).forEach(id => {
        if(els[id]) {
            els[id].addEventListener('input', e => {
                const valEl = document.getElementById(id+'Val');
                if(valEl) valEl.innerText = e.target.value;
            });
        }
    });

    const btnRun = document.getElementById('runSimBtn');
    if(btnRun) btnRun.addEventListener('click', runLiveSimulation);
    
    // Initial Chart setup
    let liveChart = null;
    const ctx = document.getElementById('liveDemandChart');
    if(ctx) {
        liveChart = new Chart(ctx, {
            type: 'bar',
            data: { labels: [], datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#8b949e' }, grid: {color: '#30363d'} },
                    y: { ticks: { color: '#e6edf3' }, grid: {color: '#30363d'}, title: {display: true, text:'Probability', color:'#8b949e'} }
                }
            }
        });
    }

    // Generate normal distribution curve for the chart
    function generateNormalDist(mean, std) {
        const labels = [];
        const data = [];
        for(let i = Math.max(0, Math.floor(mean - std * 3)); i <= Math.ceil(mean + std * 3); i++) {
            labels.push(i);
            const prob = (1 / (std * Math.sqrt(2 * Math.PI))) * Math.exp(-0.5 * Math.pow((i - mean)/std, 2));
            data.push(prob);
        }
        return {labels, data};
    }

    function renderLPText() {
        const fs = parseInt(els.fleetSize.value);
        const tc = parseInt(els.truckCost.value);
        const mfc = parseInt(els.mfCost.value);
        const ot = parseInt(els.otRate.value);
        const penalty_val = parseInt(els.penalty.value);
        const d_m = parseFloat(els.demandMean.value);
        const d_s = parseFloat(els.demandStd.value);
        
        const lpText = `
            \\[
            \\min \\sum_{i=1}^{n} (${tc} \\cdot x_i + ${mfc} \\cdot y_i + ${ot} \\cdot \\text{OT}_i) + ${penalty_val} \\cdot \\text{Overflow}
            \\]
            <div style="margin-top: 15px; background: rgba(255,255,255,0.05); padding: 12px; border-radius: 4px; border-left: 3px solid #0066ff;">
                <p style="margin: 0 0 8px 0; color: #8b949e; font-size: 0.95em; font-weight: bold; text-transform: uppercase;">Decision Variables:</p>
                <div style="color: #c9d1d9; font-size: 0.9em; display: grid; grid-template-columns: 80px 1fr; gap: 8px;">
                    <div>\\( x_i \\)</div> <div>1 if route \\( i \\) is operated by Woolworths, 0 otherwise</div>
                    <div>\\( y_i \\)</div> <div>1 if route \\( i \\) is outsourced to Mainfreight, 0 otherwise</div>
                    <div>\\( \\text{OT}_i \\)</div> <div>Hours of overtime incurred on route \\( i \\)</div>
                </div>
            </div>
            <p style="margin-top: 15px; color: #8b949e; font-size: 0.95em; font-weight: bold; text-transform: uppercase;">Subject to:</p>
            <ul style="color: #e6edf3; padding-left: 20px; line-height: 1.6; font-size: 0.95em;">
                <li>Coverage: Every store must be visited exactly once (covered by \\( x \\) or \\( y \\))</li>
                <li>Fleet Capacity: Total Woolworths routes \\( \\sum x_i \\le ${Math.floor(fs * 2)} \\) (max 2 shifts per truck)</li>
                <li>Stochastic Demand: Normal distribution with Mean = ${d_m} pallets, Std = ${d_s}</li>
            </ul>
        `;
        document.getElementById('lpContainer').innerHTML = lpText;
        if(window.MathJax) {
            MathJax.typesetPromise([document.getElementById('lpContainer')]).catch(console.error);
        }
    }

    async function runLiveSimulation() {
        const fs = parseInt(els.fleetSize.value);
        const tc = parseInt(els.truckCost.value);
        const mfc = parseInt(els.mfCost.value);
        const ot = parseInt(els.otRate.value);
        const penalty_val = parseInt(els.penalty.value);
        const d_m = parseFloat(els.demandMean.value);
        const d_s = parseFloat(els.demandStd.value);
        
        renderLPText();
        // 2. Update Demand Chart dynamically
        if(liveChart) {
            const dist = generateNormalDist(d_m, d_s);
            liveChart.data.labels = dist.labels;
            liveChart.data.datasets = [{
                label: 'Probability',
                data: dist.data,
                backgroundColor: '#0066ff',
                borderRadius: 4
            }];
            liveChart.update();
        }

        // 3. Make API call to backend
        const btnRun = document.getElementById('runSimBtn');
        const originalText = btnRun.innerHTML;
        btnRun.disabled = true;
        btnRun.innerHTML = 'Solving Master LP... (approx 8s)';
        
        try {
            const payload = {
                fleetSize: fs,
                truckCost: tc,
                mfCost: mfc,
                otRate: ot,
                penalty: penalty_val,
                demandMean: d_m,
                demandStd: d_s
            };
            
            // Fire API
            const res = await fetch('/api/run_sim', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if(!res.ok) throw new Error('API Error');
            
            // Re-fetch data.js payload dynamically and evaluate
            const dataRes = await fetch('data.js?t=' + Date.now());
            const dataText = await dataRes.text();
            
            // Execute script text in global scope synchronously
            eval(dataText);
            
            // Trigger UI reload with new data
            if(window.REPORT_DATA && window.refreshDashboard) {
                window.refreshDashboard(window.REPORT_DATA);
            }
            
            btnRun.innerHTML = 'Success!';
            
        } catch(err) {
            console.error("Simulation failed:", err);
            btnRun.innerHTML = 'Failed (Check server logs)';
        } finally {
            setTimeout(() => {
                btnRun.disabled = false;
                btnRun.innerHTML = originalText;
                lucide.createIcons();
            }, 3000);
        }
    }
    
    // Auto-initialize text at launch without running solver
    renderLPText();
});
