import socket
import _thread
import time
import json
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
    def __init__(self, wifi_client, access_point, mqtt, system, port, reset_function):
        self._sensors = []
        self._sta_if = wifi_client
        self._ap = access_point
        self.system = system
        self.mqtt = mqtt
        self.port = port
        self.reset_function = reset_function

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
                    try:
                        # Safely get sensor data
                        sensors_data = []
                        for sensor in self._sensors:
                            try:
                                sensor_info = {"name": sensor.name(), "value": sensor.value() or 0}
                                sensors_data.append(sensor_info)
                            except Exception as e:
                                print(f"Error reading sensor: {e}")
                                sensors_data.append({"name": "unknown", "value": 0})
                        status = {
                            "uptime": format_uptime(int(time.ticks_ms() / 1000)),
                            "sta_if": self._sta_if.isconnected(),
                            "ap": self._ap.active(),
                            "regulator_mode": getattr(self.system.regulator, 'mode', 'unknown'),
                            "pump": self.system.pump.status,  # Send the actual status string
                            "valve_adjusting": getattr(self.system.valve, 'adjusting', 0),
                            "valve_opening": getattr(self.system.valve, 'opening', False),
                            "valve_closing": getattr(self.system.valve, 'closing', False),
                            "valve_position": getattr(self.system.valve, 'position', 0),
                            "mqtt": getattr(self.mqtt, 'connected', False),
                            "regulation_adjustment": getattr(self.system.regulator, 'regulation_adjustment', 0),
                            "desired_temp": getattr(self.system.regulator, 'desired_secondary_supply_temp', lambda: 0)(),
                            "sensors": sensors_data,
                            "gain": getattr(self.system.regulator, 'gain', 0),
                            "offset": getattr(self.system.regulator, 'offset', 0),
                            "proportional_gain": getattr(self.system.regulator, 'proportional_gain', 0),
                        }
                        content = json.dumps(status)
                        cl.send(b'HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n')
                        cl.send(content.encode('utf-8'))
                        cl.close()
                        continue
                    except Exception as e:
                        print(f"Error in status endpoint: {e}")
                        cl.send(b'HTTP/1.0 500 Internal Server Error\r\n\r\n')
                        cl.close()
                        continue
                    continue

                # Parse control requests
                if 'GET /pump?state=on' in request:
                    self.system.pump.start()
                elif 'GET /pump?state=off' in request:
                    self.system.pump.stop()
                elif 'GET /valve?state=open' in request:
                    self.system.valve.open()
                elif 'GET /valve?state=close' in request:
                    self.system.valve.close()
                elif 'GET /regulator?state=auto' in request:
                    self.system.regulator.set_mode(Regulator.AUTOMATIC)
                elif 'GET /regulator?state=manual' in request:
                    self.system.regulator.set_mode(Regulator.MANUAL)
                elif 'GET /reset' in request:
                    self.reset_function()
                elif 'GET /set_curve_gain?state=increase' in request:
                    self.system.regulator.gain += 0.1
                elif 'GET /set_curve_gain?state=decrease' in request:
                    self.system.regulator.gain -= 0.1
                elif 'GET /set_base_temp?state=increase' in request:
                    self.system.regulator.offset += 1
                elif 'GET /set_base_temp?state=decrease' in request:
                    self.system.regulator.offset -= 1
                elif 'GET /set_proportional_gain?state=increase' in request:
                    self.system.regulator.proportional_gain += 0.1
                elif 'GET /set_proportional_gain?state=decrease' in request:
                    self.system.regulator.proportional_gain -= 0.1
                html = """<!DOCTYPE html>
<html>
<head>
<title>Heating Control</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body{font-family:Arial;margin:0;background:#f5f5f5}
.container{max-width:800px;margin:10px auto;padding:10px}
.card{background:#fff;border-radius:8px;padding:15px;margin:10px 0;box-shadow:0 2px 5px rgba(0,0,0,0.1)}
h1,h2{margin:0 0 10px 0;color:#333}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.item{background:#f8f9fa;padding:10px;border-radius:5px;border-left:3px solid #ddd}
.online{border-left-color:#4caf50}
.offline{border-left-color:#f44336}
.warning{border-left-color:#ff9800}
.label{font-size:12px;color:#666;margin-bottom:3px}
.value{font-weight:bold}
button{padding:5px 10px;border:none;border-radius:3px;margin:2px;cursor:pointer;font-size:12px}
.on{background:#4caf50;color:white}
.off{background:#f44336;color:white}
.auto{background:#9c27b0;color:white}
.manual{background:#607d8b;color:white}
.open{background:#2196f3;color:white}
.close{background:#ff9800;color:white}
.reset{background:#e91e63;color:white}
.sensors{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px}
.sensor{background:#667eea;color:white;padding:15px;border-radius:5px;text-align:center}
.temp{font-size:18px;font-weight:bold}
.valve-bar{width:100%;height:15px;background:#eee;border-radius:7px;overflow:hidden;margin:5px 0}
.valve-fill{height:100%;background:#4caf50;transition:width 0.3s}
@media(max-width:600px){.grid{grid-template-columns:1fr}.sensors{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class="container">
<h1>Heating Control</h1>

<div class="card">
<h2>System</h2>
<div class="grid">
<div class="item"><div class="label">Uptime</div><div class="value" id="uptime">...</div>
<button class="reset" onclick="sendAction('reset')">RESTART</button></div>
<div class="item" id="net"><div class="label">Network</div><div class="value" id="network">...</div></div>
<div class="item" id="reg"><div class="label">Mode</div><div class="value" id="mode">...</div>
<button class="auto" onclick="sendAction('regulator','auto')">AUTO</button>
<button class="manual" onclick="sendAction('regulator','manual')">MANUAL</button></div>
<div class="item" id="mqtt"><div class="label">MQTT</div><div class="value" id="mqttstat">...</div></div>
</div>
</div>

<div class="card">
<h2>Equipment</h2>
<div class="grid">
<div class="item" id="pump"><div class="label">Pump</div><div class="value" id="pumpstat">...</div>
<button class="on" onclick="sendAction('pump','on')">START</button>
<button class="off" onclick="sendAction('pump','off')">STOP</button></div>
<div class="item" id="valve"><div class="label">Valve</div><div class="value" id="valvestat">...</div>
<div>Position: <span id="pos">0</span>/150</div>
<div class="valve-bar"><div class="valve-fill" id="fill"></div></div>
<button class="open" onclick="sendAction('valve','open')">OPEN</button>
<button class="close" onclick="sendAction('valve','close')">CLOSE</button></div>
</div>
</div>

<div class="card">
<h2>Regulation</h2>
<div class="grid">
<div class="item"><div class="label">Desired House Supply Temp</div><div class="value" id="desired_temp">...</div></div>
<div class="item"><div class="label">Regulation Adjustment</div><div class="value" id="regulation_adj">...</div></div>
<div class="item"><div class="label">Curve Gain</div><div class="value" id="curve_gain">...</div>
<button class="+0.1" onclick="sendAction('set_curve_gain','increase')">+0.1</button>
<button class="-0.1" onclick="sendAction('set_curve_gain','decrease')">-0.1</button></div>
<div class="item"><div class="label">Base Temperature</div><div class="value" id="base_temp">...</div>
<button class="+1" onclick="sendAction('set_base_temp','increase')">+1&deg;C</button>
<button class="-1" onclick="sendAction('set_base_temp','decrease')">-1&deg;C</button></div>
<div class="item"><div class="label">Proportional Gain</div><div class="value" id="proportional_gain">...</div>
<button class="+0.1" onclick="sendAction('set_proportional_gain','increase')">+0.1</button>
<button class="-0.1" onclick="sendAction('set_proportional_gain','decrease')">-0.1</button></div>
</div>
</div>

<div class="card">
<h2>Sensors</h2>
<div class="sensors" id="sensors"></div>
</div>

</div>
<script>
function sendAction(d,s){fetch('/'+d+'?state='+s).then(()=>setTimeout(update,500))}
function update(){
fetch('/status').then(r=>r.json()).then(d=>{
document.getElementById('uptime').textContent=d.uptime;
document.getElementById('network').innerHTML=(d.sta_if?'WiFi OK':'WiFi OFF')+'<br>'+(d.ap?'AP ON':'AP OFF');
document.getElementById('mode').textContent=d.regulator_mode.toUpperCase();
document.getElementById('reg').className=d.regulator_mode==='automatic'?'item online':'item warning';
document.getElementById('mqttstat').textContent=d.mqtt?'Connected':'Disconnected';
document.getElementById('mqtt').className=d.mqtt?'item online':'item offline';
document.getElementById('pumpstat').textContent=d.pump==='on'?'RUNNING':d.pump==='off'?'STOPPED':'UNKNOWN';
document.getElementById('pump').className=d.pump==='on'?'item online':d.pump==='off'?'item offline':'item warning';
let vs='IDLE';
if(d.valve_adjusting>0){
vs=d.valve_opening?'OPENING ('+d.valve_adjusting+'s)':'CLOSING ('+d.valve_adjusting+'s)';
document.getElementById('valve').className='item warning';
}else{document.getElementById('valve').className='item online'}
document.getElementById('valvestat').textContent=vs;
document.getElementById('pos').textContent=d.valve_position||0;
document.getElementById('fill').style.width=((d.valve_position||0)/150*100)+'%';
document.getElementById('desired_temp').innerHTML=(d.desired_temp||0).toFixed(1)+'&deg;C';
document.getElementById('regulation_adj').textContent=(d.regulation_adjustment||0).toFixed(2);
document.getElementById('curve_gain').innerHTML=(d.gain||0).toFixed(2);
document.getElementById('base_temp').innerHTML=(d.offset||0).toFixed(1)+'&deg;C';
document.getElementById('proportional_gain').innerHTML=(d.proportional_gain||0).toFixed(2);
let sh='';
const sensorNames={
'ambient_temp':'Outdoor Air',
'primary_supply_temp':'Heat Source In',
'primary_return_temp':'Heat Source Out',
'secondary_supply_temp':'Building Supply',
'secondary_return_temp':'Building Return'
};
for(let s of d.sensors){
let n=sensorNames[s.name]||s.name.replace(/_/g,' ').replace(/temp/g,'').trim();
sh+='<div class="sensor"><div>'+n+'</div><div class="temp">'+s.value.toFixed(1)+'&deg;C</div></div>';
}
document.getElementById('sensors').innerHTML=sh;
}).catch(e=>console.error(e))}
setInterval(update,2000);update();
</script>
</body>
</html>"""
                cl.send(b'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                cl.send(html.encode('utf-8'))
                cl.close()
            except Exception as e:
                print("HTTP Error:", e)
