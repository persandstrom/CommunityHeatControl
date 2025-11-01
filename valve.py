class Valve:
    def __init__(self, pin_open, pin_close):
        self.pin_open = pin_open
        self.pin_close = pin_close
        self.open = False
        self.close = False
        self.adjusting = 0
        self.adjust_time = 3

    def refresh(self):
        if self.adjusting > 0:
            self.adjusting -= 1
        else:
            self.pin_close.value(1)
            self.pin_open.value(1)
        if self.close:
            self.adjusting = self.adjust_time
            self.pin_close.value(0)
        elif self.open:
            self.adjusting = self.adjust_time
            self.pin_open.value(0)
        self.open = False
        self.close = False

    def step_close(self):
        if self.adjusting:
            return
        self.close = True

    def step_open(self):
        if self.adjusting:
            return
        self.open = True    
