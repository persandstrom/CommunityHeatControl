import sys
import os
import time

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

start_time = time.time()

time.ticks_ms = lambda: int((time.time() - start_time) * 1000)
time.sleep_ms = lambda t: time.sleep(t / 1000)
time.ticks_diff = lambda a, b: a - b

import pump
pump.mock_power = False
def mock_get_shelly_status():
    return {
        "result": {
            "switch:0": {
                "output": pump.mock_power,
                "aenergy": {
                    "total": 12345.67
                }
            }
        }
    }
pump.get_shelly_status = mock_get_shelly_status

def set_shelly_power(on):
    pump.mock_power = on
pump.set_shelly_power = set_shelly_power


import ds18x20
ds18x20.TEMPERATURES = {
    '1' : -8.0,
    '2' : 23.0,
    '3' : 21.8,
    '4' : 22.1,
    '5' : 23.3
}

import main
