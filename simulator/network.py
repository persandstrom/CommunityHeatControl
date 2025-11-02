class WLAN:
    def __init__(self, type):
        self.type = type
        self.is_active = False

        def _ipconfig(arg):
            if self.is_active:
                return ('1.1.1.1')
            return None
        self.ipconfig = _ipconfig

    def active(self, is_active=None):
        if is_active:
            self.is_active = is_active
        return self.is_active

    def connect(self, ssid, password):
        if self.is_active and self.type == WLAN.IF_STA:
            print(f"Connecting to SSID: {ssid} with password: {password}")
            # Simulate connection logic here
            return True
        else:
            print("WLAN is not active or not in station mode.")
            return False

    def isconnected(self):
        # Simulate checking connection status
        return self.is_active

    def ipconfig(self):
        if self.is_active:
            return ('<ip_address>', '<subnet_mask>', '<gateway>')
    
    def ifconfig(self):
        if self.is_active:
            return ('<ip_address>', '<subnet_mask>', '<gateway>', '<dns_server>')

    def config(self, **kwargs):
        for key, value in kwargs.items():
            print(f"Setting {key} to {value}")

WLAN.IF_STA = 'station'


AP_IF = 'access_point'
AUTH_WPA_WPA2_PSK = 'WPA/WPA2-PSK'