import json
import time

from pump import Pump
from regulator import Regulator

class PersistentState:
    def __init__(self):
        self.state = {
            'valve_position': 0,
            'pump_status': Pump.ON,
            'regulator_mode': Regulator.MANUAL,
            'curve_gain': 1.0,
            'base_temp': 30.0,
            'proportional_gain': 1.0
        }
        self.save_time = time.ticks_ms()
        self.has_changes = False

    def update(self, system):

        new_state = {
            'valve_position': system.valve.position,
            'pump_status': system.pump.status,
            'regulator_mode': system.regulator.mode,
            'curve_gain': system.regulator.gain,
            'base_temp': system.regulator.offset,
            'proportional_gain': system.regulator.proportional_gain
        }

        self.has_changes = self.has_changes or (new_state != self.state)
        self.state = new_state

        # save at most once every 10 minutes
        if ( self.has_changes
             and time.ticks_diff(time.ticks_ms(), self.save_time) > 600000):
            self.save()

    def save(self):
        try:
            with open("state.json", "w", encoding="utf-8") as f:
                json.dump(self.state, f)
            self.save_time = time.ticks_ms()
            self.has_changes = False
        except OSError as e:
            print(f"Failed to save state: {e}")

    def load(self):
        try:
            with open("state.json", "r", encoding="utf-8") as f:
                self.state = json.load(f)
                self.save_time = time.ticks_ms()
                self.has_changes = False
        except (OSError, ValueError) as e:
            print(f"Failed to load state, using defaults: {e}")
