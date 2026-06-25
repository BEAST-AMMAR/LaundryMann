document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const odorSensor = document.getElementById('odor-sensor');
    const uvSensor = document.getElementById('uv-sensor');
    
    // Screens/States
    const emptyState = document.getElementById('empty-state');
    const resultsContainer = document.getElementById('results-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    // Result Elements
    const visionFeed = document.getElementById('vision-feed');
    const latencyVal = document.getElementById('latency-ms');
    const fabricVal = document.getElementById('fabric-val');
    const fabricConf = document.getElementById('fabric-conf');
    const colorVal = document.getElementById('color-val');
    const colorConf = document.getElementById('color-conf');
    const stainVal = document.getElementById('stain-val');
    
    // Routing & Alerts
    const sensorAlert = document.getElementById('sensor-alert');
    const routingBin = document.getElementById('routing-bin');
    const instructions = document.getElementById('instructions');
    const washTemp = document.getElementById('wash-temp');
    const washCycle = document.getElementById('wash-cycle');
    const washDetergent = document.getElementById('wash-detergent');

    let selectedFile = null;

    // ─── Drag & Drop Handlers ───────────────────────────────────────
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file.');
            return;
        }

        selectedFile = file;
        const textContainer = dropZone.querySelector('.drop-zone-text');
        textContainer.innerHTML = `<span>${file.name}</span><br>Ready for scan`;
        
        const icon = dropZone.querySelector('.drop-zone-icon');
        icon.innerHTML = `<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;
        
        analyzeBtn.disabled = false;
        
        // Hide empty state immediately, but keep results hidden until analysis
        emptyState.classList.add('hidden');
        resultsContainer.classList.add('hidden');

        // Show raw image preview immediately
        const reader = new FileReader();
        reader.onload = (e) => {
            visionFeed.src = e.target.result;
            // Show results container so vision feed is visible, but clear old metrics
            resultsContainer.classList.remove('hidden');
            resetMetrics();
        };
        reader.readAsDataURL(file);
    }

    function resetMetrics() {
        latencyVal.textContent = "—";
        fabricVal.textContent = "—";
        fabricConf.textContent = "—";
        colorVal.textContent = "—";
        colorConf.textContent = "—";
        stainVal.textContent = "—";
        routingBin.textContent = "Awaiting Route...";
        instructions.textContent = "—";
        washTemp.textContent = "—";
        washCycle.textContent = "—";
        washDetergent.textContent = "—";
        sensorAlert.classList.add('hidden');
    }

    // ─── AI Pipeline Execution ──────────────────────────────────────
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // Show loading state
        loadingOverlay.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('odor_detected', odorSensor.checked);
        formData.append('uv_fluorescence', uvSensor.checked);

        const startTime = performance.now();

        try {
            const response = await fetch('http://localhost:8000/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`API returned ${response.status}`);
            }

            const data = await response.json();
            const latency = Math.round(performance.now() - startTime);
            updateUI(data, latency);

        } catch (error) {
            console.error('Error during analysis:', error);
            alert('Analysis failed. Ensure the NEXUS backend server (FastAPI) is running on port 8000.');
        } finally {
            loadingOverlay.classList.add('hidden');
            resultsContainer.classList.remove('hidden');
        }
    });

    function updateUI(data, latency) {
        if (data.status !== 'success') return;

        // Update Vision Feed if annotated image is provided
        if (data.annotated_image) {
            visionFeed.src = 'data:image/jpeg;base64,' + data.annotated_image;
        }

        // Latency
        latencyVal.textContent = `${latency}ms`;

        // Ensemble Metrics
        fabricVal.textContent = data.analysis.fabric.prediction;
        fabricConf.textContent = `${(data.analysis.fabric.confidence * 100).toFixed(1)}%`;
        
        colorVal.textContent = data.analysis.color.prediction;
        colorConf.textContent = `${(data.analysis.color.confidence * 100).toFixed(1)}%`;
        
        stainVal.textContent = data.analysis.stains_detected;

        // Sensor Overrides
        if (data.sensors.odor_detected || data.sensors.uv_fluorescence_detected) {
            sensorAlert.classList.remove('hidden');
            const sensorType = data.sensors.odor_detected ? "E-Nose (VOC)" : "UV Multispectral";
            sensorAlert.querySelector('span').textContent = `SENSOR OVERRIDE · ${sensorType} — All visual routing bypassed. Rerouted to specialized handling.`;
        } else {
            sensorAlert.classList.add('hidden');
        }

        // Routing Decision
        routingBin.textContent = data.decision.routing_bin;
        instructions.innerHTML = `<strong>Parameters:</strong> ${data.decision.instructions}`;

        // Wash Cycle Recommendations (Local frontend mapping based on bin)
        const washRecs = {
            "BIN_A": { cycle: "Standard Wash", temp: "40°C", det: "Standard Powder Detergent" },
            "BIN_B": { cycle: "Heavy Duty", temp: "60°C", det: "Heavy Enzyme Pre-Treat" },
            "BIN_C": { cycle: "Cold Wash", temp: "20°C", det: "Color-Safe Liquid" },
            "BIN_D": { cycle: "Stain Cycle", temp: "30°C", det: "Oxygen Booster" },
            "BIN_E": { cycle: "Delicate", temp: "30°C", det: "Mild Gentle Liquid" },
            "BIN_F": { cycle: "Sanitize / Ozone", temp: "Cold", det: "Ozone Module" },
            "BIN_G": { cycle: "Manual Inspection", temp: "N/A", det: "Manual Spot Clean" }
        };

        const rec = washRecs[data.decision.routing_bin] || washRecs["BIN_G"];
        
        washTemp.textContent = rec.temp;
        washCycle.textContent = rec.cycle;
        washDetergent.textContent = `Pre-treat: ${rec.det}`;
    }
});
