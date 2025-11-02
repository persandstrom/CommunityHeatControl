class PIDRegulator:
    def __init__(self, expected_delta_t, integral_gain, derivative_gain):
        self._expected_dt = expected_delta_t  # Expected time interval between calls

        # Base parameters (tuned for 1 second interval)
        base_ki = integral_gain
        base_kd = derivative_gain

        self._kp = 1.0                           # Proportional constant (frequency independent)
        self._ki = base_ki * expected_delta_t    # Scale Ki with time interval
        self._kd = base_kd / expected_delta_t    # Scale Kd inversely with time interval

        self.integral_sum = 0.0      # Sum of all errors
        self.previous_error = 0.0    # Previous error
        self._max_integral = 100.0    # Maximum absolute value for integral sum to prevent windup

    def reset(self):
        self.integral_sum = 0.0
        self.previous_error = 0.0

    def compute(self, set_point, process_variable):

        # Calculate error
        error = set_point - process_variable

        # Use expected delta time (assumes constant interval)
        delta_time = self._expected_dt

        # Proportional term
        p_term = self._kp * error

        # Integral term
        self.integral_sum += error * delta_time
        self.integral_sum = max(-self._max_integral, min(self._max_integral, self.integral_sum))
        i_term = self._ki * self.integral_sum

        # Derivative term
        d_term = self._kd * (error - self.previous_error) / delta_time

        # Update for next computation
        self.previous_error = error

        # Control output
        output = p_term + i_term + d_term
        
        return output