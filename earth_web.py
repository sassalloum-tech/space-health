from flask import Flask, render_template_string
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ascis_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Earth Mission Control · HUD</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body { 
            background-color: #050505; 
            background-image: url('{{ url_for('static', filename='background.jpg') }}');
            background-size: cover;
            background-position: center;
            color: #00ffcc; 
            font-family: 'Share Tech Mono', monospace; 
            margin: 0; padding: 20px; 
            display: flex; flex-direction: column; align-items: center;
            overflow: hidden;
        }
        
        .overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(5, 5, 5, 0.75); z-index: -1;
        }

        .header { 
            font-family: 'Orbitron', sans-serif; font-size: 24px; font-weight: bold; 
            text-shadow: 0 0 15px #00ffcc; margin-bottom: 20px; 
            display: flex; justify-content: space-between; width: 98%; 
            border-bottom: 2px solid rgba(0, 255, 204, 0.5); padding-bottom: 10px;
        }
        
        .clock { color: #ffcc00; text-shadow: 0 0 10px #ffcc00; }
        
        .grid-container { display: grid; grid-template-columns: 1.2fr 1fr 1fr; gap: 20px; width: 98%; }
        
        .panel { 
            border: 1px solid rgba(0, 255, 204, 0.4); 
            border-left: 4px solid #00ffcc;
            border-radius: 5px; background: rgba(10, 10, 10, 0.85); 
            padding: 15px; box-shadow: 0 0 15px rgba(0,255,204,0.1); 
            backdrop-filter: blur(5px);
        }
        .panel h2 { margin-top: 0; font-size: 14px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 5px; text-transform: uppercase; color: #fff; }
        
        .critical-panel { border-color: #ff3333; box-shadow: 0 0 20px rgba(255,51,51,0.4); border-left: 4px solid #ff3333; }
        .critical-panel h2 { color: #ff3333; text-shadow: 0 0 10px #ff3333; }
        
        .row { display: flex; justify-content: space-between; padding: 5px 0; font-size: 13px; border-bottom: 1px dashed rgba(0, 255, 204, 0.2); }
        .val { font-weight: bold; color: #fff; }
        
        .heart-container { width: 100%; height: 200px; position: relative; }
        
        .ecg-line { width: 100%; height: 60px; margin-top: 10px; }
        
        .outcome-box { background: rgba(0, 0, 0, 0.5); padding: 10px; margin-top: 10px; border-left: 3px solid #00ffcc; font-size: 13px; }
        .outcome-box.red { border-left-color: #ff3333; }
        
        .hidden { display: none; }
    </style>
</head>
<body>
    <div class="overlay"></div>

    <div class="header">
        <span>EARTH MISSION CONTROL · HUD</span>
        <span class="clock" id="earthClock">Earth Sync: --:--:--</span>
    </div>
    
    <div class="grid-container">
        <!-- COLUMN 1: The 3D Heart & ECG -->
        <div>
            <div class="panel" id="actualHeartPanel">
                <h2>ACTUAL ASTRONAUT HEART (DIGITAL TWIN)</h2>
                <div id="actualHeart" class="heart-container"></div>
                <svg class="ecg-line" viewBox="0 0 500 100" preserveAspectRatio="none">
                    <polyline id="ecgWave" fill="none" stroke="#00ffcc" stroke-width="2" 
                    points="0,50 50,50 60,20 70,80 80,50 150,50 160,20 170,80 180,50 250,50 260,20 270,80 280,50 350,50 360,20 370,80 380,50 450,50 460,20 470,80 480,50 500,50" />
                </svg>
            </div>
            
            <div class="panel" style="margin-top: 15px;">
                <h2>CARDIAC METRICS</h2>
                <div class="row"><span>HEART RATE:</span> <span class="val" id="valHR">--</span></div>
                <div class="row"><span>BLOOD PRESS:</span> <span class="val" id="valBP">--</span></div>
                <div class="row"><span>EJECTION FRACTION (EF):</span> <span class="val" id="valEF">58%</span></div>
                <div class="row"><span>CARDIAC OUTPUT:</span> <span class="val" id="valCO">3.5 L/min</span></div>
                <div class="row"><span>STATUS:</span> <span class="val" id="valStatus">--</span></div>
            </div>
        </div>

        <!-- COLUMN 2: Prediction & AI Explainability -->
        <div>
            <div class="panel">
                <h2>PREDICTION ENGINE</h2>
                <div class="row"><span>VF RISK:</span> <span class="val" id="predVF">2%</span></div>
                <div class="row"><span>SHOCK RISK:</span> <span class="val" id="predShock">3%</span></div>
                <div class="row"><span>HEART FAILURE:</span> <span class="val" id="predHF">1%</span></div>
                <div style="text-align: right; margin-top: 15px; font-weight: bold;" id="predTrend">TREND: STABLE</div>
            </div>
            
            <div class="panel hidden" id="aiExplainPanel" style="margin-top: 15px; border-color: #ff3333;">
                <h2>AI EXPLAINABILITY</h2>
                <div class="row"><span>ECG ST ELEVATION</span> <span class="val">+40%</span></div>
                <div class="row"><span>TROPONIN RISE</span> <span class="val">+35%</span></div>
                <div class="row"><span>WALL MOTION DEFECT</span> <span class="val">+13%</span></div>
                <div style="text-align: center; margin-top: 15px; font-weight: bold; color: #ff3333; text-shadow: 0 0 10px #ff3333;">CONFIDENCE: 98%</div>
            </div>

            <div class="panel hidden" id="outcomePanel" style="margin-top: 15px;">
                <h2>OUTCOME PROJECTION</h2>
                <div class="outcome-box">
                    <b>CURRENT THERAPY</b><br>
                    Survival ........ 94%<br>
                    EF Recovery ..... 54%
                </div>
                <div class="outcome-box red">
                    <b>WITHOUT THERAPY</b><br>
                    Survival ........ 41%<br>
                    EF Recovery ..... 29%
                </div>
            </div>
        </div>

        <!-- COLUMN 3: Environment & Relay -->
        <div>
            <div class="panel">
                <h2>LIFE SUPPORT & ENVIRONMENT</h2>
                <div class="row"><span>RESPIRATION RATE:</span> <span class="val" id="valResp">16 bpm</span></div>
                <div class="row"><span>SPO2:</span> <span class="val" id="valSpo2">98%</span></div>
                <div class="row"><span>CABIN PRESSURE:</span> <span class="val">14.7 psi</span></div>
                <div class="row"><span>CABIN O2:</span> <span class="val">21.0%</span></div>
                <div class="row"><span>RADIATION:</span> <span class="val" style="color:#ffcc00;">0.45 mSv</span></div>
            </div>

            <div class="panel" style="margin-top: 15px;">
                <h2>🛰 IMRVS RELAY STATION</h2>
                <div class="row"><span>PACKET ID:</span> <span class="val" id="relayPacket">----</span></div>
                <div class="row"><span>INTEGRITY:</span> <span class="val">100%</span></div>
                <div class="row"><span>ARCHIVED:</span> <span class="val" style="color:#00ffcc;">YES</span></div>
                <div class="row"><span>EARTH RECEIPT:</span> <span class="val" id="relayStatus" style="color:#ffcc00;">PENDING</span></div>
            </div>
            
            <div class="panel" style="margin-top: 15px;">
                <h2>EARTH-MARS DELAY</h2>
                <div class="row"><span>MARS LIVE:</span> <span class="val" style="color: #ff3333;" id="marsClock">--:--:--</span></div>
                <div class="row"><span>EARTH COPY:</span> <span class="val" id="earthDelayClock">--:--:--</span></div>
                <div style="text-align: center; margin-top: 15px; font-weight: bold; color: #ffcc00; text-shadow: 0 0 10px #ffcc00;">DATA AGE: 22 MINUTES</div>
            </div>
        </div>
    </div>

    <script>
        // 1. Clocks
        setInterval(() => {
            const now = new Date();
            document.getElementById('earthClock').innerText = "Earth Sync: " + now.toLocaleTimeString();
            document.getElementById('marsClock').innerText = now.toLocaleTimeString();
            const delayed = new Date(now.getTime() - 22 * 60000);
            document.getElementById('earthDelayClock').innerText = delayed.toLocaleTimeString();
        }, 1000);

        // 2. WebSockets
        const socket = io();
        
        socket.on('telemetry', function(data) {
            document.getElementById('valHR').innerText = data.heart_rate + " BPM";
            document.getElementById('valBP').innerText = data.blood_pressure;
            document.getElementById('valSpo2').innerText = data.spo2 + "%";
            document.getElementById('valResp').innerText = data.resp_rate + " bpm";
            document.getElementById('valEF').innerText = data.ejection_fraction + "%";
            document.getElementById('valCO').innerText = data.cardiac_output + " L/min";
            
            document.getElementById('relayPacket').innerText = Math.floor(Math.random() * 9000) + 1000;

            if (data.status === 'CRITICAL') {
                document.getElementById('actualHeartPanel').classList.add('critical-panel');
                document.getElementById('valStatus').innerText = "STEMI DETECTED";
                document.getElementById('valStatus').style.color = "#ff3333";
                
                document.getElementById('aiExplainPanel').classList.remove('hidden');
                document.getElementById('outcomePanel').classList.remove('hidden');
                document.getElementById('predVF').innerText = "12%";
                document.getElementById('predShock').innerText = "17%";
                document.getElementById('predHF').innerText = "8%";
                document.getElementById('predTrend').innerText = "TREND: ▲ WORSENING";
                document.getElementById('predTrend').style.color = "#ff3333";
                
                document.getElementById('ecgWave').setAttribute('stroke', '#ff3333');
            } else {
                document.getElementById('actualHeartPanel').classList.remove('critical-panel');
                document.getElementById('valStatus').innerText = "STABLE";
                document.getElementById('valStatus').style.color = "#00ffcc";
                
                document.getElementById('aiExplainPanel').classList.add('hidden');
                document.getElementById('outcomePanel').classList.add('hidden');
                document.getElementById('predVF').innerText = "2%";
                document.getElementById('predShock').innerText = "3%";
                document.getElementById('predHF').innerText = "1%";
                document.getElementById('predTrend').innerText = "TREND: ▼ STABLE";
                document.getElementById('predTrend').style.color = "#00ffcc";
                
                document.getElementById('ecgWave').setAttribute('stroke', '#00ffcc');
            }
            
            if(window.updateHeart3D) window.updateHeart3D(data.status === 'CRITICAL', data.heart_rate);
        });

        // 3. 3D Wireframe Heart
        function createHeart(containerId, baseColor, isActual) {
            const container = document.getElementById(containerId);
            if (!container) return;
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            container.appendChild(renderer.domElement);

            const heartGroup = new THREE.Group();
            const material = new THREE.MeshBasicMaterial({ color: baseColor, wireframe: true });
            
            const vent = new THREE.Mesh(new THREE.ConeGeometry(1.2, 2, 32), material); vent.rotation.x = Math.PI; vent.position.y = -0.5; heartGroup.add(vent);
            const leftLobe = new THREE.Mesh(new THREE.SphereGeometry(0.8, 32, 32), material); leftLobe.position.set(-0.6, 1, 0); heartGroup.add(leftLobe);
            const rightLobe = new THREE.Mesh(new THREE.SphereGeometry(0.8, 32, 32), material); rightLobe.position.set(0.6, 0.8, 0); heartGroup.add(rightLobe);
            
            scene.add(heartGroup);
            camera.position.z = 5;

            let bpm = 72;
            function animate() {
                requestAnimationFrame(animate);
                const t = Date.now() * 0.001;
                const beat = 1 + Math.sin(t * (bpm / 60) * Math.PI * 2) * 0.08;
                heartGroup.scale.set(beat, beat, beat);
                heartGroup.rotation.y = Math.sin(t * 0.5) * 0.3;
                renderer.render(scene, camera);
            }
            animate();

            if (isActual) {
                window.updateHeart3D = function(isCritical, newBpm) {
                    material.color.setHex(isCritical ? 0xff3333 : 0x00ffcc);
                    bpm = newBpm;
                }
            }
        }
        createHeart("actualHeart", 0x00ffcc, true);    
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    import os
    if not os.path.exists('static'):
        os.makedirs('static')
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)
