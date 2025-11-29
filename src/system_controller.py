class SystemController:
    def __init__(self, regulator, pump, valve, ambient_temp, primary_supply_temp,
                 primary_return_temp, secondary_supply_temp, secondary_return_temp):
        self.regulator = regulator
        self.pump = pump
        self.valve = valve
        self.ambient_temp = ambient_temp
        self.primary_supply_temp = primary_supply_temp
        self.primary_return_temp = primary_return_temp
        self.secondary_supply_temp = secondary_supply_temp
        self.secondary_return_temp = secondary_return_temp
