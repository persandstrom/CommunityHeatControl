
""" Main program for district heating controller """

import json
import time
import gc
import network
from machine import Pin
from umqtt.simple import MQTTClient
from temp_sensor import TempSensors
from mqtt_controller import MQTTController
from http_view import HTTPView
from valve import Valve
from led import Led
from regulator import Regulator
from pump import Pump


with open("settings.json") as f:
    settings = json.load(f)

print("Set up LEDs")
main_led = Led(13)
pump_led = Led(14)
valve_led = Led(15)
mqtt_led = Led(16)

print("Set up Station")
sta_if = network.WLAN(network.WLAN.IF_STA)
sta_if.active(True)
print(f"Network active: {sta_if.active()}")

print("Set up MQTT Client")
mqtt = MQTTClient(
    client_id=settings["mqtt"]["client_id"],
    server=settings["mqtt"]["broker"],
    user=settings["mqtt"]["user"],
    password=settings["mqtt"]["password"])

def ensure_connections():
    try:
        if not sta_if.isconnected():
            sta_if.connect(settings["station"]["ssid"], settings["station"]["password"])
            print(f"Network connected {sta_if.isconnected()}")
            print(f"IP: {sta_if.ipconfig('addr4')}")
        if sta_if.isconnected() and not mqtt.connected:
            mqtt.connect()
    except Exception:
        pass # Ignore exceptions during reconnect attempts

# Set up network
print("Set up Access point")
ap = network.WLAN(network.AP_IF)
ap.active(False) # Reset if active
ap.active(True)
ap.config(essid=settings["access_point"]["ssid"],
          password=settings["access_point"]["password"],
          authmode=network.AUTH_WPA_WPA2_PSK)
print('Access Point Active: ', ap.ifconfig())

print("Set up pump")
pump = Pump(pump_led, ap)

print("Set up Temp Sensors")
temp_sensors = TempSensors(32, 33)
ambient_temp = temp_sensors.get_sensor(0, "ambient_temp")
primary_supply_temp = temp_sensors.get_sensor(1, "primary_supply_temp")
primary_return_temp = temp_sensors.get_sensor(2, "primary_return_temp")
secondary_supply_temp = temp_sensors.get_sensor(3, "secondary_supply_temp")
secondary_return_temp = temp_sensors.get_sensor(4, "secondary_return_temp")

print("Set up Valve")
pin_open_valve = Pin(19, Pin.OUT, value=1)
pin_close_valve = Pin(18, Pin.OUT, value=1)
valve = Valve(
    pin_open_valve,
    pin_close_valve)
valve.full_close()

print("set up Regulator")
regulator = Regulator(
    primary_supply_temp=primary_supply_temp,
    secondary_supply_temp=secondary_supply_temp,
    ambient_temp=ambient_temp,
    valve=valve,
    pump=pump)

print("set up MQTT Controller")
mqtt = MQTTController(
    mqtt=mqtt,
    regulator=regulator,
    topic_prefix="district_heating",
    led=mqtt_led)
mqtt.add_sensor(ambient_temp)
mqtt.add_sensor(primary_supply_temp)
mqtt.add_sensor(primary_return_temp)
mqtt.add_sensor(secondary_supply_temp)
mqtt.add_sensor(secondary_return_temp)

print("set up HTTP View")
http_v = HTTPView(
    sta_if,
    ap,
    regulator=regulator,
    pump=pump,
    mqtt=mqtt,
    valve=valve, 
    port=settings["web_server"]["port"])
http_v.add_sensor(ambient_temp)
http_v.add_sensor(primary_supply_temp)
http_v.add_sensor(primary_return_temp)
http_v.add_sensor(secondary_supply_temp)
http_v.add_sensor(secondary_return_temp)
http_v.start()

print("Starting main loop")
loop_time = 1000 # ms
while True:
    start_loop_time = time.ticks_ms()
    main_led.switch()
    pump.refresh()
    valve.refresh()
    temp_sensors.scan()
    mqtt.execute()
    regulator.regulate()
    ensure_connections()
    gc.collect()
    loop_time = time.ticks_ms() - start_loop_time
    print(f"loop time: {loop_time}")
    sleep_time = max(0, 1000 - loop_time)
    time.sleep_ms(sleep_time)
