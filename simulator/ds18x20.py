TEMPERATURES = {}


class DS18X20:
    def __init__(self, pin):
        self.pin = pin

    def scan(self):
        # Simulate scanning for devices on the bus
        return list(TEMPERATURES.keys())

    def read_temp(self, rom):
        # Simulate reading temperature from a device
        return TEMPERATURES.get(rom, None)

    def set_temp(self, rom, temp):
        # Simulate setting a temperature for a device
        TEMPERATURES[rom] = temp

    def convert_temp(self):
        # Simulate temperature conversion process
        pass
