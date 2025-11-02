from pump import Pump
from pid_regulator import PIDRegulator


class Regulator:
    def __init__(self, community_in_temp, circulation_in_temp, outdoor_temp, valve, pump):
        self.community_in_temp = community_in_temp
        self.circulation_in_temp = circulation_in_temp
        self.outdoor_temp = outdoor_temp
        self.valve = valve
        self.pump = pump
        self.mode = Regulator.MANUAL
        self.pid = PIDRegulator(expected_delta_t=1, integral_gain=.000, derivative_gain=0)

        self.max_community_heating_temp = 45  # Max community heating temperature
        self.adjustment_threshold = 3  # Minimum PID output to trigger valve adjustment
        self.adjustment_interval = 300  # 5 minutes = 300 seconds
        self.last_adjustment_time = self.adjustment_interval # OK to regulate immediately

    def max_outdoor_temp_for_heating_reached(self):
        return self.outdoor_temp.value() > 16

    def desired_circuit_heating_in_temp(self):
        return -1*self.outdoor_temp.value()+30

    def regulate(self):
        if self.mode == Regulator.MANUAL:
            return
        # If the outdoor temperature is above 16 degrees, turn off the pump and close the valve
        if self.max_outdoor_temp_for_heating_reached():
            self.valve.close()
            self.pump.stop()
            self.pid.reset()
            return

        # If the outdoor temperature is below or equal to 16 degrees, turn on the pump
        self.pump.start()
        regulation_adjustment = self.pid.compute(
            set_point=self.desired_circuit_heating_in_temp(),
            process_variable=self.circulation_in_temp.value()
        )

        self.last_adjustment_time += 1
        if self.last_adjustment_time <= self.adjustment_interval:
            return
        self.last_adjustment_time = 0

        # Debug PID components
        error = self.desired_circuit_heating_in_temp() - self.circulation_in_temp.value()
        print(f"Target: {self.desired_circuit_heating_in_temp()}°C, Actual: {self.circulation_in_temp.value():.2f}°C, Error: {error:.2f}°C")
        print(f"PID output: {regulation_adjustment:.2f}, Integral sum: {self.pid.integral_sum:.2f}")

        if abs(regulation_adjustment) > self.adjustment_threshold:
            print(f"Adjusting valve by {regulation_adjustment:.2f}")
            # self.valve.adjust(regulation_adjustment)


    def set_mode(self, mode):
        self.mode = mode

Regulator.MANUAL = "manual"
Regulator.AUTOMATIC = "automatic"
