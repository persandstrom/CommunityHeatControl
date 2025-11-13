from pid_regulator import PIDRegulator


class Regulator:
    def __init__(self, primary_supply_temp, secondary_supply_temp, ambient_temp, valve, pump):
        self.primary_supply_temp = primary_supply_temp
        self.secondary_supply_temp = secondary_supply_temp
        self.ambient_temp = ambient_temp
        self.valve = valve
        self.pump = pump
        self.mode = Regulator.MANUAL
        self.pid = PIDRegulator(expected_delta_t=1, integral_gain=.000, derivative_gain=0)

        # Configurable parameters
        self.adjustment_threshold = 3  # Minimum PID output to trigger valve adjustment
        self.adjustment_interval = 300  # 5 minutes = 300 seconds

        # Heating curve parameters
        self.gain = 1.0   # Positive gain: higher = steeper heating curve
        self.offset = 30.0   # Base temperature when ambient is 0°C

        # Internal state
        self.regulation_adjustment = 0
        self.last_adjustment_time = self.adjustment_interval


    def desired_secondary_supply_temp(self):
        return -1 * self.gain * self.ambient_temp.value() + self.offset

    def regulate(self):
        self.regulation_adjustment = self.pid.compute(
            set_point=self.desired_secondary_supply_temp(),
            process_variable=self.secondary_supply_temp.value()
        )

        if self.mode == Regulator.MANUAL:
            return

        # Keep pump running during heating season - manual seasonal control
        self.pump.start()

        self.last_adjustment_time += 1
        if self.last_adjustment_time <= self.adjustment_interval:
            return
        self.last_adjustment_time = 0

        # Debug PID components
        error = self.desired_secondary_supply_temp() - self.secondary_supply_temp.value()
        print(f"Target: {self.desired_secondary_supply_temp()}°C, Actual: {self.secondary_supply_temp.value():.2f}°C, Error: {error:.2f}°C")
        print(f"PID output: {self.regulation_adjustment:.2f}, Integral sum: {self.pid.integral_sum:.2f}")

        if abs(self.regulation_adjustment) > self.adjustment_threshold:
            print(f"Adjusting valve by {self.regulation_adjustment:.2f}")
            #self.valve.adjust(self.regulation_adjustment)


    def set_mode(self, mode):
        self.mode = mode

Regulator.MANUAL = "manual"
Regulator.AUTOMATIC = "automatic"
