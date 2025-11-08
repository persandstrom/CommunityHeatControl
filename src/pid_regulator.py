class PIDRegulator:
    def __init__(self, expected_delta_t, integral_gain, derivative_gain):
        self._expected_dt = expected_delta_t

        self._kp = 1.0
        self._ki = integral_gain * expected_delta_t
        self._kd = derivative_gain / expected_delta_t

        self.integral_sum = 0.0
        self.previous_error = 0.0
        self._max_integral = 100.0

    def reset(self):
        self.integral_sum = 0.0
        self.previous_error = 0.0

    def compute(self, set_point, process_variable):

        error = set_point - process_variable
        proportional_term = self._kp * error

        # Calculate integral term
        self.integral_sum += error * self._expected_dt
        self.integral_sum = max(
            -self._max_integral,
            min(self._max_integral, self.integral_sum))
        integral_term = self._ki * self.integral_sum

        # Calculate derivative term
        derivative_term = self._kd * (error - self.previous_error) / self._expected_dt

        self.previous_error = error

        output = proportional_term + integral_term + derivative_term

        return output
