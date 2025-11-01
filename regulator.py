from pump import Pump


class Regulator:
    def __init__(self, community_in_temp, circulation_in_temp, outdoor_temp, valve, pump):
        self.community_in_temp = community_in_temp
        self.circulation_in_temp = circulation_in_temp
        self.outdoor_temp = outdoor_temp
        self.valve = valve
        self.pump = pump
        self.mode = Regulator.MANUAL

    def regulate(self):
        if self.mode == Regulator.MANUAL:
            return

    def set_mode(self, mode):
        self.mode = mode

Regulator.MANUAL = "manual"
Regulator.AUTOMATIC = "automatic"
