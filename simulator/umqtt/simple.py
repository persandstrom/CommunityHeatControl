class MQTTClient:
    def __init__(self, client_id, server, port=1883, user=None, password=None, keepalive=60):
        self.client_id = client_id
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.keepalive = keepalive
        self.connected = False

    def connect(self):
        # Simulate connecting to the MQTT broker
        pass

    def disconnect(self):
        # Simulate disconnecting from the MQTT broker
        pass

    def publish(self, topic, msg, qos=0):
        # Simulate publishing a message to a topic
        pass

    def subscribe(self, topic, qos=0):
        # Simulate subscribing to a topic
        pass

    def check_msg(self):
        # Simulate checking for incoming messages
        pass
