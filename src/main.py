""" Main program """

import json
import time
import gc
import network
from machine import Pin
from temp_sensor import TempSensors
from mqtt_controller import MQTTController
from http_view import HTTPView
from valve import Valve
from led import Led
from regulator import Regulator
from pump import Pump
from persistent_state import PersistentState
import machine
from system_controller import SystemController


with open("settings.json") as f:
    settings = json.load(f)

persistent_state = PersistentState()
persistent_state.load()

print("Set up LEDs")
main_led = Led(13)
pump_led = Led(14)
valve_led = Led(15)
mqtt_led = Led(16)

print("Set up wifi client")
wifi_client = network.WLAN(network.WLAN.IF_STA)
wifi_client.active(True)
print(f"Network active: {wifi_client.active()}")

def ensure_connections():
    try:
        if not wifi_client.isconnected():
            wifi_client.connect(settings["station"]["ssid"], settings["station"]["password"])
            print(f"Network connected {wifi_client.isconnected()}")
            print(f"IP: {wifi_client.ipconfig('addr4')}")
        if wifi_client.isconnected() and not mqtt.connected:
            mqtt.connect()
    except Exception:
        pass # Ignore exceptions during reconnect attempts

# Set up network
print("Set up Access point")
access_point = network.WLAN(network.AP_IF)
access_point.active(False) # Reset if active
access_point.active(True)
access_point.config(essid=settings["access_point"]["ssid"],
          password=settings["access_point"]["password"],
          authmode=network.AUTH_WPA_WPA2_PSK)
print('Access Point Active: ', access_point.ifconfig())

print("Set up pump")
pump = Pump(access_point)
if persistent_state.state["pump_status"] == Pump.ON:
    pump.start()
elif persistent_state.state["pump_status"] == Pump.OFF:
    pump.stop()

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
valve.position = persistent_state.state["valve_position"]

print("set up Regulator")
regulator = Regulator(
    primary_supply_temp=primary_supply_temp,
    secondary_supply_temp=secondary_supply_temp,
    ambient_temp=ambient_temp,
    valve=valve,
    pump=pump)
regulator.mode = persistent_state.state["regulator_mode"]
regulator.gain = persistent_state.state["curve_gain"]
regulator.offset = persistent_state.state["base_temp"]
regulator.proportional_gain = persistent_state.state["proportional_gain"]

system = SystemController(
    regulator=regulator,
    pump=pump,
    valve=valve,
    ambient_temp=ambient_temp,
    primary_supply_temp=primary_supply_temp,
    primary_return_temp=primary_return_temp,
    secondary_supply_temp=secondary_supply_temp,
    secondary_return_temp=secondary_return_temp)

print("set up MQTT Controller")
mqtt = MQTTController(
    mqtt_settings=settings["mqtt"],
    system=system)

def cleanup():
    try:
        access_point.active(False)
        wifi_client.active(False)
        persistent_state.update(system)
        persistent_state.save()
        print("Shutdown complete")
    except Exception as e:
        print(f"Error during shutdown: {e}")


def reset():
    """Perform cleanup before reset"""
    cleanup()
    machine.reset()

print("set up HTTP View")
http_v = HTTPView(
    wifi_client,
    access_point,
    mqtt = mqtt,
    system=system,
    port=settings["web_server"]["port"],
    reset_function=reset)
http_v.add_sensor(ambient_temp)
http_v.add_sensor(primary_supply_temp)
http_v.add_sensor(primary_return_temp)
http_v.add_sensor(secondary_supply_temp)
http_v.add_sensor(secondary_return_temp)
http_v.start()

print("Starting main loop")
loop_time = 1000 # ms
try:
    while True:
        start_loop_time = time.ticks_ms()
        main_led.switch()
        pump.refresh()
        if pump.status == Pump.UNKNOWN:
            pump_led.on()
        else:
            pump_led.switch()
        valve.refresh()
        temp_sensors.scan()
        mqtt.execute()
        if mqtt.connected:
            mqtt_led.switch()
        else:
            mqtt_led.on()
        regulator.regulate()
        ensure_connections()
        persistent_state.update(system)
        gc.collect()
        loop_time = time.ticks_ms() - start_loop_time
        print(f"loop time: {loop_time}")
        sleep_time = max(0, 1000 - loop_time)
        time.sleep_ms(sleep_time)

except KeyboardInterrupt:
    print("Stopping...")
    cleanup()


except Exception as e:
    # Other errors - clean shutdown and reset
    print(f"Unexpected error: {e}")
    print("Performing reset...")
    reset()
