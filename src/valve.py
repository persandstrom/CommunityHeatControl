class Valve:
    """
    Controls a motorized valve actuator using two digital output pins.
    
    The valve position is tracked internally as a value between 0 (fully closed)
    and 150 (fully open), where each unit represents one second of motor travel time.
    
    The valve is controlled by two pins:
    - pin_open: Activates the opening motor (active low)
    - pin_close: Activates the closing motor (active low)
    
    The refresh() method must be called once per second from the main loop
    to update the valve position and control the motor pins.
    """

    def __init__(self, pin_open, pin_close):
        """
        Initialize the Valve controller.

        Args:
            pin_open: Digital output pin connected to the valve opening motor (active low)
            pin_close: Digital output pin connected to the valve closing motor (active low)
        """
        self.pin_open = pin_open
        self.pin_close = pin_close
        self.opening = False
        self.closing = False
        self.adjusting = 0
        self.position = 0

    def refresh(self):
        """
        Update valve state. Must be called once per second from the main loop.
        """
        if self.adjusting > 0:
            self.adjusting = max(0, self.adjusting - 1)
        else:
            self.pin_close.value(1)
            self.pin_open.value(1)
            self.opening = False
            self.closing = False
        if self.closing:
            self.position = max(0, self.position - 1)
            self.pin_close.value(0)
        elif self.opening:
            self.position = min(150, self.position + 1)
            self.pin_open.value(0)

    def adjust(self, amount):
        """
        Adjust valve position by a relative amount.
        """
        if amount < 0:
            self.close(duration=int(-amount))
        elif amount > 0:
            self.open(duration=int(amount))

    def close(self, duration=1):
        """
        Close the valve by running the closing motor for the specified duration.
        """
        if self.adjusting:
            return

        # If closing would reach or pass fully closed position
        # add extra time to ensure complete closure
        if self.position <= duration:
            duration = max(self.position + 5, duration)

        self.adjusting = duration
        self.closing = True

    def open(self, duration=1):
        """
        Close the valve by running the closing motor for the specified duration.
        """
        if self.adjusting or self.position >= 150:
            return
        self.adjusting = duration
        self.opening = True
