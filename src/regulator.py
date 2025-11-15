
class Regulator:
    def __init__(self, primary_supply_temp, secondary_supply_temp, ambient_temp, valve, pump):
        self.primary_supply_temp = primary_supply_temp
        self.secondary_supply_temp = secondary_supply_temp
        self.ambient_temp = ambient_temp
        self.valve = valve
        self.pump = pump
        self.mode = Regulator.MANUAL

        # Configurable parameters
        self.adjustment_threshold = 3  # Minimum error output to trigger valve adjustment
        self.adjustment_interval = 300  # 5 minutes = 300 seconds
        self.proportional_gain = 1.0

        # Heating curve parameters
        self.gain = 1.0   # Positive gain: higher = steeper heating curve
        self.offset = 30.0   # Base temperature when ambient is 0°C

        # Internal state
        self.regulation_adjustment = 0
        self.last_adjustment_time = self.adjustment_interval


    def desired_secondary_supply_temp(self):
        return -1 * self.gain * self.ambient_temp.value() + self.offset

    def regulate(self):

        # P-Regulation
        error = self.desired_secondary_supply_temp() - self.secondary_supply_temp.value()
        self.regulation_adjustment = self.proportional_gain * error


        if self.mode == Regulator.MANUAL:
            return

        # Keep pump running while in automatic mode
        self.pump.start()

        self.last_adjustment_time += 1
        if self.last_adjustment_time <= self.adjustment_interval:
            return
        self.last_adjustment_time = 0

        if abs(self.regulation_adjustment) > self.adjustment_threshold:
            self.valve.adjust(self.regulation_adjustment)


    def set_mode(self, mode):
        self.mode = mode

Regulator.MANUAL = "manual"
Regulator.AUTOMATIC = "automatic"
