import socket
import _thread
import time
import json
import traceback
import machine

from pump import Pump
from regulator import Regulator

def format_uptime(seconds):
    SECS_PER_MIN = 60
    SECS_PER_HOUR = 3600
    SECS_PER_DAY = 86400

    days = seconds / SECS_PER_DAY
    seconds %= SECS_PER_DAY
    hours = seconds // SECS_PER_HOUR
    seconds %= SECS_PER_HOUR
    minutes = seconds // SECS_PER_MIN
    seconds %= SECS_PER_MIN

    return f"{days:.0f}d {hours:.0f}h {minutes:.0f}m {seconds:.0f}s"

class HTTPView:
    def __init__(self, sta_if, ap, regulator, pump, mqtt, valve, port):
        self._sensors = []
        self._sta_if = sta_if
        self._ap = ap
        self.regulator = regulator
        self.pump = pump
        self.mqtt = mqtt
        self.valve = valve
        self.port = port

    def start(self):
        _thread.start_new_thread(self._serve, ())

    def add_sensor(self, sensor):
        self._sensors.append(sensor)

    def _serve(self):
        try:
            addr = socket.getaddrinfo('0.0.0.0', self.port)[0][-1]
            s = socket.socket()
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(addr)
            s.listen(1)
        except Exception as e:
            print("Could not start webserver: " + str(e))
            return
        while True:
            try:
                cl, addr = s.accept()
                request = cl.recv(1024).decode()
                # Handle AJAX status request
                if "GET /status" in request:
                    status = {
                        "uptime": format_uptime(int(time.ticks_ms() / 1000)),
                        "sta_if": self._sta_if.isconnected(),
                        "ap": self._ap.isconnected(),
                        "regulator_mode": self.regulator.mode,
                        "pump": self.pump.status == Pump.ON,
                        "valve_adjusting": self.valve.adjusting,
                        "valve_opening": self.valve.opening,
                        "valve_closing": self.valve.closing,
                        "valve_position": self.valve.position,
                        "mqtt": self.mqtt.connected,
                        "sensors": [
                            {"name": sensor.name(), "value": sensor.value()}
                            for sensor in self._sensors
                        ]
                    }
                    content = json.dumps(status)
                    cl.send(b'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n')
                    cl.send(bytes(content, 'utf-8'))
                    cl.close()
                    continue

                # Parse control requests
                if 'GET /pump?state=on' in request:
                    self.pump.start()
                elif 'GET /pump?state=off' in request:
                    self.pump.stop()
                elif 'GET /valve?state=open' in request:
                    self.valve.open()
                elif 'GET /valve?state=close' in request:
                    self.valve.close()
                elif 'GET /regulator?state=auto' in request:
                    self.regulator.set_mode(Regulator.AUTOMATIC)
                elif 'GET /regulator?state=manual' in request:
                    self.regulator.set_mode(Regulator.MANUAL)
                elif 'GET /reset' in request:
                    machine.reset()

                # Build main page
                html = """
                <html>
                <head>
                    <title>Community Heating System</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        * { box-sizing: border-box; }
                        body { 
                            font-family: 'Segoe UI', Arial, sans-serif; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            margin: 0; 
                            min-height: 100vh;
                        }
                        .container { max-width: 1200px; margin: 20px auto; padding: 0 20px; }
                        .header { text-align: center; color: white; margin-bottom: 30px; }
                        .header h1 { font-size: 2.5em; margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
                        .header .subtitle { opacity: 0.9; margin-top: 10px; font-size: 1.1em; }
                        
                        .grid { display: flex; flex-direction: column; gap: 20px; }
                        .card { 
                            background: rgba(255,255,255,0.95); 
                            border-radius: 15px; 
                            box-shadow: 0 8px 32px rgba(0,0,0,0.1); 
                            padding: 25px; 
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255,255,255,0.2);
                        }
                        .card h2 { margin-top: 0; color: #333; font-size: 1.4em; border-bottom: 2px solid #eee; padding-bottom: 10px; }
                        
                        .status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
                        .status-item { 
                            background: #f8f9fa; 
                            padding: 15px; 
                            border-radius: 10px; 
                            border-left: 4px solid #ddd;
                            transition: all 0.3s ease;
                        }
                        .status-item.online { border-left-color: #4caf50; }
                        .status-item.offline { border-left-color: #f44336; }
                        .status-item.warning { border-left-color: #ff9800; }
                        
                        .status-label { font-size: 0.9em; color: #666; margin-bottom: 5px; }
                        .status-value { font-size: 1.1em; font-weight: 600; display: flex; flex-direction: column; }
                        .status-value > div { margin: 2px 0; display: flex; align-items: center; }
                        
                        .actions { margin-top: 10px; }
                        .actions button { 
                            padding: 8px 16px; 
                            border: none; 
                            border-radius: 20px; 
                            margin: 2px; 
                            cursor: pointer; 
                            font-weight: 500;
                            transition: all 0.3s ease;
                            font-size: 0.9em;
                        }
                        .actions button:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
                        .actions .on { background: #4caf50; color: white; }
                        .actions .off { background: #f44336; color: white; }
                        .actions .open { background: #2196f3; color: white; }
                        .actions .close { background: #ff9800; color: white; }
                        .actions .auto { background: #9c27b0; color: white; }
                        .actions .manual { background: #607d8b; color: white; }
                        .actions .reset { background: #e91e63; color: white; }
                        
                        .sensor-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
                        .sensor-card {
                            background: linear-gradient(135deg, #667eea, #764ba2);
                            color: white;
                            padding: 20px;
                            border-radius: 12px;
                            text-align: center;
                            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                        }
                        .sensor-name { font-size: 0.9em; opacity: 0.9; margin-bottom: 5px; }
                        .sensor-value { font-size: 1.8em; font-weight: 600; }
                        .sensor-unit { font-size: 0.8em; opacity: 0.8; }
                        
                        .valve-display {
                            background: #f8f9fa;
                            padding: 15px;
                            border-radius: 10px;
                            text-align: center;
                            margin: 10px 0;
                        }
                        .valve-bar {
                            width: 100%;
                            height: 20px;
                            background: #e0e0e0;
                            border-radius: 10px;
                            overflow: hidden;
                            margin: 10px 0;
                        }
                        .valve-fill {
                            height: 100%;
                            background: linear-gradient(90deg, #4caf50, #2196f3);
                            border-radius: 10px;
                            transition: width 0.3s ease;
                        }
                        
                        @media (max-width: 768px) {
                            .status-grid { grid-template-columns: 1fr; }
                            .sensor-grid { grid-template-columns: 1fr 1fr; }
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Community Heating Control</h1>
                            <div class="subtitle">Real-time monitoring and control system</div>
                        </div>
                        
                        <div class="grid">
                            <div class="card">
                                <h2>System Status</h2>
                                <div class="status-grid">
                                    <div class="status-item" id="uptime-card">
                                        <div class="status-label">System Uptime</div>
                                        <div class="status-value" id="uptime">...</div>
                                        <div class="actions">
                                            <button class="reset" onclick="sendAction('reset')">RESTART</button>
                                        </div>
                                    </div>
                                    
                                    <div class="status-item" id="network-card">
                                        <div class="status-label">Network Status</div>
                                        <div class="status-value">
                                            <div id="sta_if" style="margin-bottom: 8px;">...</div>
                                            <div id="ap">...</div>
                                        </div>
                                    </div>
                                    
                                    <div class="status-item" id="regulator-card">
                                        <div class="status-label">Regulator Mode</div>
                                        <div class="status-value" id="regulator_mode">...</div>
                                        <div class="actions">
                                            <button class="auto" onclick="sendAction('regulator', 'auto')">AUTO</button>
                                            <button class="manual" onclick="sendAction('regulator', 'manual')">MANUAL</button>
                                        </div>
                                    </div>
                                    
                                    <div class="status-item" id="mqtt-card">
                                        <div class="status-label">MQTT Connection</div>
                                        <div class="status-value" id="mqtt_status">...</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h2>Equipment Control</h2>
                                <div class="status-grid">
                                    <div class="status-item" id="pump-card">
                                        <div class="status-label">Heat Pump</div>
                                        <div class="status-value" id="pump_status">...</div>
                                        <div class="actions">
                                            <button class="on" onclick="sendAction('pump', 'on')">START</button>
                                            <button class="off" onclick="sendAction('pump', 'off')">STOP</button>
                                        </div>
                                    </div>
                                    
                                    <div class="status-item" style="grid-column: span 2;" id="valve-card">
                                        <div class="status-label">Control Valve</div>
                                        <div class="status-value" id="valve_status">...</div>
                                        <div class="valve-display">
                                            <div>Position: <span id="valve_position">0</span>/150</div>
                                            <div class="valve-bar">
                                                <div class="valve-fill" id="valve_fill" style="width: 0%"></div>
                                            </div>
                                        </div>
                                        <div class="actions">
                                            <button class="open" onclick="sendAction('valve', 'open')">OPEN</button>
                                            <button class="close" onclick="sendAction('valve', 'close')">CLOSE</button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="card">
                                <h2>Temperature Sensors</h2>
                                <div class="sensor-grid" id="sensor_grid">
                                    <!-- Sensors will be populated here -->
                                </div>
                            </div>
                        </div>
                    </div>
                    <script>
                        function sendAction(device, state) {
                            fetch('/' + device + '?state=' + state)
                                .then(() => setTimeout(updateStatus, 500));
                        }
                        
                        function updateStatus() {
                            fetch('/status')
                                .then(resp => resp.json())
                                .then(data => {
                                    // Update uptime
                                    document.getElementById('uptime').textContent = data.uptime;
                                    
                                    // Update network status
                                    document.getElementById('sta_if').innerHTML = data.sta_if
                                        ? 'WiFi Connected'
                                        : 'WiFi Disconnected';
                                    document.getElementById('ap').innerHTML = data.ap
                                        ? 'AP Active'
                                        : 'AP Inactive';
                                    
                                    // Update regulator mode with styling
                                    const regulatorCard = document.getElementById('regulator-card');
                                    document.getElementById('regulator_mode').textContent = data.regulator_mode.toUpperCase();
                                    regulatorCard.className = data.regulator_mode === 'automatic' ? 'status-item online' : 'status-item warning';
                                    
                                    // Update pump status
                                    const pumpCard = document.getElementById('pump-card');
                                    document.getElementById('pump_status').innerHTML = data.pump
                                        ? 'RUNNING'
                                        : 'STOPPED';
                                    pumpCard.className = data.pump ? 'status-item online' : 'status-item offline';
                                    
                                    // Update valve status with improved display
                                    const valveCard = document.getElementById('valve-card');
                                    let valveStatus = '';
                                    if (data.valve_adjusting > 0) {
                                        if (data.valve_opening) {
                                            valveStatus = 'OPENING (' + data.valve_adjusting + 's)';
                                            valveCard.className = 'status-item warning';
                                        } else if (data.valve_closing) {
                                            valveStatus = 'CLOSING (' + data.valve_adjusting + 's)';
                                            valveCard.className = 'status-item warning';
                                        }
                                    } else {
                                        valveStatus = 'IDLE';
                                        valveCard.className = 'status-item online';
                                    }
                                    document.getElementById('valve_status').innerHTML = valveStatus;
                                    
                                    // Update valve position and bar
                                    const position = data.valve_position || 0;
                                    document.getElementById('valve_position').textContent = position;
                                    const percentage = (position / 150) * 100;
                                    document.getElementById('valve_fill').style.width = percentage + '%';
                                    
                                    // Update MQTT status
                                    const mqttCard = document.getElementById('mqtt-card');
                                    document.getElementById('mqtt_status').innerHTML = data.mqtt
                                        ? 'Connected'
                                        : 'Disconnected';
                                    mqttCard.className = data.mqtt ? 'status-item online' : 'status-item offline';
                                    
                                    // Update sensors with new card layout
                                    let sensorHtml = '';
                                    for (const sensor of data.sensors) {
                                        const temp = sensor.value || 0;
                                        const displayName = sensor.name.replace(/_/g, ' ').replace(/temp/g, '').trim();
                                        sensorHtml += `
                                            <div class="sensor-card">
                                                <div class="sensor-name">${displayName}</div>
                                                <div class="sensor-value">${temp.toFixed(1)}<span class="sensor-unit">&deg;C</span></div>
                                            </div>
                                        `;
                                    }
                                    document.getElementById('sensor_grid').innerHTML = sensorHtml;
                                })
                                .catch(err => {
                                    console.error('Failed to update status:', err);
                                });
                        }
                        
                        // Update every second
                        setInterval(updateStatus, 1000);
                        // Initial update
                        updateStatus();
                    </script>
                </body>
                </html>
                """
                cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                cl.send(bytes(html, 'utf-8'))
                cl.close()
            except Exception as e:
                print("Error:", e, traceback.format_exc())
