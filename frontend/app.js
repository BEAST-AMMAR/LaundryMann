document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const captureCamBtn = document.getElementById('capture-cam-btn');
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
    const robotCoords = document.getElementById('robot-coords');
    const dispatchRobotBtn = document.getElementById('dispatch-robot-btn');

    let selectedFile = null;
    let lastBinId = null;

    // Relative API Base
    const API_BASE = window.location.origin;

    // ─── Drag & Drop Handlers ───────────────────────────────────────
    if (dropZone) {
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
    }

    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });
    }

    function handleFileSelect(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select a valid image file.');
            return;
        }

        selectedFile = file;
        const textContainer = dropZone.querySelector('.drop-zone-text');
        if (textContainer) {
            textContainer.innerHTML = `<span>${file.name}</span><br>Ready for scan`;
        }
        
        analyzeBtn.disabled = false;
        
        if (emptyState) emptyState.classList.add('hidden');
        if (resultsContainer) resultsContainer.classList.add('hidden');

        const reader = new FileReader();
        reader.onload = (e) => {
            visionFeed.src = e.target.result;
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
        if (robotCoords) robotCoords.textContent = "—";
        sensorAlert.classList.add('hidden');
    }

    // ─── Hardware Camera Direct Capture ─────────────────────────────
    if (captureCamBtn) {
        captureCamBtn.addEventListener('click', async () => {
            loadingOverlay.classList.remove('hidden');
            try {
                const res = await fetch(`${API_BASE}/hardware/camera/capture`);
                const data = await res.json();
                if (data.status === 'success' && data.image_base64) {
                    visionFeed.src = 'data:image/jpeg;base64,' + data.image_base64;
                    emptyState.classList.add('hidden');
                    resultsContainer.classList.remove('hidden');
                    resetMetrics();
                    // Auto analyze live frame
                    executeAnalysis(null);
                }
            } catch (err) {
                console.error("Failed to capture from hardware camera:", err);
                alert("Hardware camera unavailable. Please check physical connection or use file upload.");
            } finally {
                loadingOverlay.classList.add('hidden');
            }
        });
    }

    // ─── AI Pipeline Execution ──────────────────────────────────────
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', () => {
            executeAnalysis(selectedFile);
        });
    }

    async function executeAnalysis(file) {
        loadingOverlay.classList.remove('hidden');
        const formData = new FormData();
        if (file) {
            formData.append('file', file);
        }
        formData.append('odor_detected', odorSensor ? odorSensor.checked : false);
        formData.append('uv_fluorescence', uvSensor ? uvSensor.checked : false);

        const startTime = performance.now();

        try {
            const response = await fetch(`${API_BASE}/analyze`, {
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
            alert('Analysis failed. Ensure the NEXUS backend server is online.');
        } finally {
            loadingOverlay.classList.add('hidden');
            resultsContainer.classList.remove('hidden');
        }
    }

    function updateUI(data, latency) {
        if (data.status !== 'success') return;

        // Update Vision Feed with bounding boxes
        if (data.annotated_image) {
            visionFeed.src = 'data:image/jpeg;base64,' + data.annotated_image;
        }

        latencyVal.textContent = `${latency}ms`;

        // Ensemble Metrics
        fabricVal.textContent = data.analysis.fabric.prediction;
        fabricConf.textContent = `${(data.analysis.fabric.confidence * 100).toFixed(0)}%`;
        
        colorVal.textContent = data.analysis.color.color_name || data.analysis.color.prediction;
        colorConf.textContent = `Bleed: ${data.analysis.color.bleed_risk || 'LOW'}`;
        
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
        lastBinId = data.decision.routing_bin;
        routingBin.textContent = `${data.decision.routing_bin} · ${data.decision.bin_name || ''}`;
        instructions.innerHTML = `<strong>Parameters:</strong> ${data.decision.instructions}`;

        const recipe = data.decision.recipe;
        if (recipe) {
            washTemp.textContent = recipe.temp;
            washCycle.textContent = recipe.cycle;
            washDetergent.textContent = recipe.detergent;
        }

        // Robotic Arm Trajectory Parameters
        if (data.robotics && robotCoords) {
            const p = data.robotics.grasp_parameters.pick_coords_mm;
            const d = data.robotics.target_drop_coords;
            robotCoords.innerHTML = `Pick: [${p.x}, ${p.y}, ${p.z}]mm → Drop: [${d.x}, ${d.y}, ${d.z}]mm | Grip: ${data.robotics.grasp_parameters.grip_force_n}N`;
        }

        if (dispatchRobotBtn) {
            dispatchRobotBtn.disabled = false;
        }
    }

    // ─── Robotic Arm Dispatch Trigger ───────────────────────────────
    if (dispatchRobotBtn) {
        dispatchRobotBtn.addEventListener('click', async () => {
            if (!lastBinId) return;
            dispatchRobotBtn.disabled = true;
            dispatchRobotBtn.textContent = "Dispatched...";
            try {
                const formData = new FormData();
                formData.append('bin_id', lastBinId);
                const res = await fetch(`${API_BASE}/robot/dispatch`, {
                    method: 'POST',
                    body: formData
                });
                const rdata = await res.json();
                alert(`Robotic Arm executed cycle #${rdata.dispatch_packet.cycle_id} in ${rdata.dispatch_packet.cycle_duration_ms}ms!`);
            } catch (err) {
                console.error("Robotic dispatch failed:", err);
            } finally {
                dispatchRobotBtn.disabled = false;
                dispatchRobotBtn.textContent = "Execute Robotic Pick & Place";
            }
        });
    }
});
