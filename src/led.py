from machine import Pin

class Led:
    def __init__(self, pin_nr):
        self.pin = Pin(pin_nr, Pin.OUT, value=1)
        self.is_on = True

    def on(self):
        self.is_on = True
        self.pin.value(1)

    def off(self):
        self.is_on = False
        self.pin.value(0)

    def switch(self):
        if self.is_on:
            self.pin.value(0)
            self.is_on = False
        else:
            self.pin.value(1)
            self.is_on = True
