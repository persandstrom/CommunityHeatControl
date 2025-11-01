
""" Main program for district heating controller """
import time
import network
import json

from machine import Pin

from umqtt.simple import MQTTClient

from temp_sensor import TempSensorArray
from mqtt_controller import MQTTController
from http_view import HTTPView
from valve import Valve
from led import Led
from regulator import Regulator
from pump import Pump


with open("settings.json") as f:
    settings = json.load(f)

# Set up LEDs
main_led = Led(13)
pump_led = Led(14)
valve_led = Led(2)
mqtt_led = Led(16)

# Set up network
# Station Mode
sta_if = network.WLAN(network.WLAN.IF_STA)
sta_if.active(True)
print(f"Network active: {sta_if.active()}")
sta_if.connect(settings["station"]["ssid"], settings["station"]["password"])

# Wait for networks
while not sta_if.isconnected():
    print("waiting for network")
    time.sleep(1)
print(f"Network connected {sta_if.isconnected()}")
print(f"IP: {sta_if.ipconfig('addr4')}")



## Set up MQTT Client
mqtt = MQTTClient(
    client_id=settings["mqtt"]["client_id"],
    server=settings["mqtt"]["broker"],
    user=settings["mqtt"]["user"],
    password=settings["mqtt"]["password"])
try:
    mqtt.connect()
except Exception as e:
    print("MQTT Connection failed: ", e)

# Set up network
# Access point mode
ap = network.WLAN(network.AP_IF)
ap.active(False) # Reset if active
ap.active(True)
ap.config(essid=settings["access_point"]["ssid"],
          password=settings["access_point"]["password"],
          authmode=network.AUTH_WPA_WPA2_PSK)
print('Access Point Active: ', ap.ifconfig())

pump = Pump(pump_led)

#Set up Sensors
ts = TempSensorArray(32, 33)
outdoor_temp = ts.get_sensor(0, "outdoor_temp")
community_in_temp = ts.get_sensor(1, "community_in_temp")
community_out_temp = ts.get_sensor(2, "community_out_temp")
circulation_in_temp = ts.get_sensor(3, "circulation_in_temp")
circulation_out_temp = ts.get_sensor(4, "circulation_out_temp")

# Set up valve
pin_open_valve = Pin(17, Pin.OUT, value=1) 
pin_close_valve = Pin(18, Pin.OUT, value=1)
valve = Valve(
    pin_open_valve,
    pin_close_valve)

# valve.full_close()

regulator = Regulator(
    community_in_temp=community_in_temp,
    circulation_in_temp=circulation_in_temp,
    outdoor_temp=outdoor_temp,
    valve=valve,
    pump=pump)



# Set up MQTT Controller
mqtt = MQTTController(
    mqtt=mqtt,
    regulator=regulator,
    topic_prefix="district_heating",
    led=mqtt_led)
mqtt.connect()
mqtt.add_sensor(outdoor_temp)
mqtt.add_sensor(community_in_temp)
mqtt.add_sensor(community_out_temp)
mqtt.add_sensor(circulation_in_temp)
mqtt.add_sensor(circulation_out_temp)


# Set up HTTP View
http_v = HTTPView(
    sta_if,
    ap,
    regulator=regulator,
    pump=pump,
    mqtt=mqtt,
    valve=valve)
http_v.add_sensor(outdoor_temp)
http_v.add_sensor(community_in_temp)
http_v.add_sensor(community_out_temp)
http_v.add_sensor(circulation_in_temp)
http_v.add_sensor(circulation_out_temp)
http_v.start()


loop_time = 1000 # ms
while True:
    start_loop_time = time.ticks_ms()
    main_led.switch()
    pump.refresh()
    valve.refresh()
    mqtt.execute()
    regulator.regulate()
    loop_time = time.ticks_ms() - start_loop_time
    print(f"loop time: {loop_time}") 
    sleep_time = max(0, 1000 - loop_time)
    time.sleep_ms(sleep_time)
