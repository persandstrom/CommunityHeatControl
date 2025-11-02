
class Pin:
    def __init__(self, pin_nr, direction='input', value=0):
        self.pin_nr = pin_nr
        self.direction = direction
        self.internal_value = value

    def value(self, value):
        if self.direction != 'output':
            raise ValueError("Cannot set value on an input pin")
        self.internal_value = value

    def get_value(self):
        if self.direction != 'input':
            raise ValueError("Cannot get value from an output pin")
        return self.internal_value
    

def reset():
    print("Machine reset called")

Pin.OUT = 'output'
Pin.IN = 'input'