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

    def close(self, duration=3):
        if self.adjusting or self.position <= 0:
            return
        self.adjusting = duration
        self.closing = True

    def full_close(self):
        self.opening = False
        self.closing = True
        self.adjusting = 150

    def open(self, duration=3):
        if self.adjusting or self.position >= 150:
            return
        self.adjusting = duration
        self.opening = True
