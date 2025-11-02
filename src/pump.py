import requests


SHELLY_IP = "192.168.4.2"


def get_shelly_status():
    url = f"http://{SHELLY_IP}/rpc"
    payload = {
        "id": 1,
        "method": "Shelly.GetStatus"
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception("Failed to read shelly status")
    status_data = response.json()
    response.close()
    return status_data

def set_shelly_power(on):
    url = f"http://{SHELLY_IP}/rpc"
    payload = {
        "id": 1,
        "method": "Switch.Set",
        "params": {
            "id": 0,
            "on": on
        }
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        response.close()
        return result
    except Exception as e:
        print(f"Error toggling power: {e}")
        return None


class Pump:
    def __init__(self, led):
        self.status = Pump.UNKNOWN
        self.wanted_state = Pump.UNKNOWN
        self.power = None
        self.led = led
        self.refreshing = False

    def refresh(self):
        if self.refreshing:
            return # Do not refresh if already ongoing
        self._refresh()

    def _refresh(self):
        if self.wanted_state != Pump.UNKNOWN and self.wanted_state != self.status:
            set_shelly_power(self.wanted_state == Pump.ON)

        self.refreshing = True
        try:
            status_data = get_shelly_status()
            self.status = Pump.ON if status_data["result"]["switch:0"]["output"] else Pump.OFF
            self.power = status_data["result"]["switch:0"]["aenergy"]['total']
        except Exception as e:
            print(e)
            self.status = Pump.UNKNOWN
            self.power = None

        if self.power is not None and not self.status == Pump.UNKNOWN:
            self.led.switch()
        else:
            self.led.on()
        self.refreshing = False

    def start(self):
        self.wanted_state = Pump.ON

    def stop(self):
        self.wanted_state = Pump.OFF


Pump.ON = "on"
Pump.OFF = "off"
Pump.UNKNOWN = "unknown"
