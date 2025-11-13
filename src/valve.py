class Valve:
    def __init__(self, pin_open, pin_close):
        self.pin_open = pin_open
        self.pin_close = pin_close
        self.opening = False
        self.closing = False
        self.adjusting = 0
        self.position = 0

    def refresh(self):
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

    def close(self, duration=1):
        if self.adjusting or self.position <= 0:
            return

        # If closing would reach or pass fully closed position
        # add extra time to ensure complete closure
        if self.position <= duration:
            duration = self.position + 5

        self.adjusting = duration
        self.closing = True

    def open(self, duration=1):
        if self.adjusting or self.position >= 150:
            return
        self.adjusting = duration
        self.opening = True
