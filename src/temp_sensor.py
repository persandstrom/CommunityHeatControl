from machine import Pin
import ds18x20
import onewire


class TempSensor():
    def __init__(self, temp_sensor_array, index, name):
        self._temp_sensor_array = temp_sensor_array
        self._index = index
        self._name = name

    def value(self):
        return self._temp_sensor_array.temperatures[self._index]

    def name(self):
        return self._name

class TempSensors():
    def __init__(self, *ports):
        self._ds_array = []
        self._roms_array = []

        for port in ports:
            one_wire = onewire.OneWire(Pin(port))
            ds_array = ds18x20.DS18X20(one_wire)
            self._ds_array.append(ds_array)
            self._roms_array.append(ds_array.scan())

        self.temperatures = [25] * sum(len(roms) for roms in self._roms_array)

        for ds in self._ds_array:
            ds.convert_temp()

    def get_sensor(self, index, name):
        return TempSensor(self, index, name)

    def scan(self):
        try:
            sensor_index = 0
            for ids, ds in enumerate(self._ds_array):
                for roms in self._roms_array[ids]:
                    self.temperatures[sensor_index] = ds.read_temp(roms)
                    sensor_index = sensor_index + 1
            for ds in self._ds_array:
                ds.convert_temp()
        except Exception as e:
            print(f"Error reading temperature sensors: {e}")
