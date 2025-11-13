import json
import time

from pump import Pump
from regulator import Regulator

class PersistentState:
    def __init__(self):
        self.valve_position = 0
        self.pump_status = Pump.ON  # Safer default - pump running
        self.regulator_mode = Regulator.MANUAL  # Default to manual mode
        self.curve_gain = 1.0
        self.base_temp = 30.0
        self.save_time = time.ticks_ms()  # More reliable for intervals


    def update(self, valve_position, pump_status, regulator_mode, curve_gain, base_temp):
        # Check if any value has changed
        has_changes = (valve_position != self.valve_position or
                      pump_status != self.pump_status or
                      regulator_mode != self.regulator_mode or
                      curve_gain != self.curve_gain or
                      base_temp != self.base_temp)

        if not has_changes:
            return  # No changes, do not save

        # Check time throttling - save at most once every 10 minutes
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.save_time) < 600000:  # 10 minutes in ms
            return  # Too soon since last save

        # Update values
        self.valve_position = valve_position
        self.pump_status = pump_status
        self.regulator_mode = regulator_mode
        self.curve_gain = curve_gain
        self.base_temp = base_temp

        self.save()

    def save(self):
        state = {
            "valve_position": self.valve_position,
            "pump_status": self.pump_status,
            "regulator_mode": self.regulator_mode,
            "curve_gain": self.curve_gain,
            "base_temp": self.base_temp
        }
        try:
            with open("state.json", "w", encoding="utf-8") as f:
                json.dump(state, f)
            self.save_time = time.ticks_ms()
        except OSError as e:
            print(f"Failed to save state: {e}")

    def load(self):
        try:
            with open("state.json", "r", encoding="utf-8") as f:
                state = json.load(f)
                self.valve_position = state.get("valve_position", 0)
                self.pump_status = state.get("pump_status", Pump.ON)
                self.regulator_mode = state.get("regulator_mode", Regulator.MANUAL)
                self.curve_gain = state.get("curve_gain", 1.0)
                self.base_temp = state.get("base_temp", 30.0)
                self.save_time = time.ticks_ms()
        except (OSError, ValueError) as e:
            print(f"Failed to load state, using defaults: {e}")
            # Use default values already set in constructor
