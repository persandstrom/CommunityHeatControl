import socket
import _thread
import time
import json
import machine

from pump import Pump

class HTTPView:
    def __init__(self, sta_if, ap, regulator, pump, mqtt, valve):
        self._sensors = []
        self._sta_if = sta_if
        self._ap = ap
        self.regulator = regulator
        self.pump = pump
        self.mqtt = mqtt
        self.valve = valve

    def start(self):
        _thread.start_new_thread(self._serve, ())

    def add_sensor(self, sensor):
        self._sensors.append(sensor)

    def _serve(self):
        try:
            addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
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
                        "uptime": int(time.ticks_ms() / 1000),
                        "sta_if": self._sta_if.isconnected(),
                        "ap": self._ap.isconnected(),
                        "regulator_mode": self.regulator.mode,
                        "pump": self.pump.status == Pump.ON,
                        "valve": self.valve.adjusting,
                        "mqtt": self.mqtt.connected,
                        "sensors": [
                            {"name": sensor.name(), "value": sensor.value()}
                            for sensor in self._sensors
                        ]
                    }
                    content = json.dumps(status)
                    cl.send('HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n')
                    cl.send(content)
                    cl.close()
                    continue

                # Parse control requests
                if 'GET /pump?state=on' in request:
                    self.pump.start()
                elif 'GET /pump?state=off' in request:
                    self.pump.stop()
                elif 'GET /valve?state=open' in request:
                    self.valve.step_open()
                elif 'GET /valve?state=close' in request:
                    self.valve.step_close()
                elif 'GET /reset' in request:
                    machine.reset()

                # Build main page
                html = """
                <html>
                <head>
                    <title>Community Heating System</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <style>
                        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; margin: 0; }
                        .container { max-width: 600px; margin: 40px auto; }
                        .card { background: #fff; border-radius: 12px; box-shadow: 0 4px 14px #bbb; padding: 30px; margin-bottom: 30px; }
                        h1 { font-size: 2em; margin-bottom: 10px; }
                        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                        th, td { text-align: left; padding: 12px 8px; }
                        tr:nth-child(even) { background: #f8f9fa; }
                        th { background: #0078d7; color: #fff; }
                        .actions button { padding: 10px 18px; border: none; border-radius: 5px; margin: 3px; cursor: pointer; font-weight: bold; }
                        .actions .on { background: #4caf50; color: white; }
                        .actions .off { background: #f44336; color: white; }
                        .actions .open { background: #2196f3; color: white; }
                        .actions .close { background: #ff9800; color: white; }
                        .actions .reset { background: #ff9800; color: white; }
                        .status-dot { display:inline-block; width:12px; height:12px; border-radius:50%; margin-right:6px; }
                        .dot-on { background:#4caf50; }
                        .dot-off { background:#f44336; }
                        .dot-open { background:#2196f3; }
                        .dot-close { background:#ff9800; }
                        .sensor-table th { background: #444; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="card">
                            <h1>Heating</h1>
                            <table>
                                <tr><th>Key</th><th>Value</th></tr>
                                <tr>
                                    <td>Uptime</td>
                                    <td>
                                        <span id="uptime">...</span>
                                        <span class="actions">
                                            <button class="reset" onclick="sendAction('reset')">RESET</button>
                                        </span>
                                    </td>
                                </tr>
                                <tr><td>STA_IF</td><td id="sta_if">...</td></tr>
                                <tr><td>AP</td><td id="ap">...</td></tr>
                                <tr><td>Regulator Mode</td><td id="regulator_mode">...</td></tr>
                                <tr>
                                    <td>Pump</td>
                                    <td>
                                        <span id="pump_status"></span>
                                        <span class="actions">
                                            <button class="on" onclick="sendAction('pump', 'on')">ON</button>
                                            <button class="off" onclick="sendAction('pump', 'off')">OFF</button>
                                        </span>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Valve</td>
                                    <td>
                                        <span id="valve_status"></span>
                                        <span class="actions">
                                            <button class="open" onclick="sendAction('valve', 'open')">OPEN</button>
                                            <button class="close" onclick="sendAction('valve', 'close')">CLOSE</button>
                                        </span>
                                    </td>
                                </tr>
                                <tr><td>MQTT Connected</td><td id="mqtt_status">...</td></tr>
                            </table>
                        </div>
                        <div class="card">
                            <h2>Sensors</h2>
                            <table class="sensor-table">
                                <tr><th>Sensor</th><th>Value</th></tr>
                                <tbody id="sensor_rows"></tbody>
                            </table>
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
                                    document.getElementById('uptime').textContent = data.uptime + 's';
                                    document.getElementById('sta_if').innerHTML = data.sta_if
                                        ? '<span class="status-dot dot-on"></span>Connected'
                                        : '<span class="status-dot dot-off"></span>Disconnected';
                                    document.getElementById('ap').innerHTML = data.ap
                                        ? '<span class="status-dot dot-on"></span>Connected'
                                        : '<span class="status-dot dot-off"></span>Disconnected';
                                    document.getElementById('regulator_mode').textContent = data.regulator_mode;
                                    document.getElementById('pump_status').innerHTML = data.pump
                                        ? '<span class="status-dot dot-on"></span>ON'
                                        : '<span class="status-dot dot-off"></span>OFF';
                                    document.getElementById('valve_status').innerHTML = data.valve
                                        ? '<span class="status-dot dot-open"></span>ADJUSTING'
                                        : '<span class="status-dot dot-close"></span>IDLE';
                                    document.getElementById('mqtt_status').innerHTML = data.mqtt
                                        ? '<span class="status-dot dot-on"></span>Connected'
                                        : '<span class="status-dot dot-off"></span>Disconnected';
                                    let rows = '';
                                    for (const s of data.sensors) {
                                        rows += `<tr><td>${s.name}</td><td>${s.value.toFixed(2)}</td></tr>`;
                                    }
                                    document.getElementById('sensor_rows').innerHTML = rows;
                                });
                        }
                        setInterval(updateStatus, 1000);
                        updateStatus();
                    </script>
                </body>
                </html>
                """
                cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                cl.send(html)
                cl.close()
            except Exception as e:
                print(e)
