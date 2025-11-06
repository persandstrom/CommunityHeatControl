from regulator import Regulator


class MQTTController:
    def __init__(self, mqtt, regulator, topic_prefix, led):
        self.client = mqtt
        self.regulator = regulator
        self.topic_prefix = topic_prefix
        self.sensors = []
        self.connected = False
        self.led = led

    def connect(self):
        try:
            self.client.connect()
            self.client.set_callback(self.incomming_message)
            self.client.subscribe(f"{self.topic_prefix}/set_mode")
            self.connected = True
            print("MQTT Connected")
        except:
            self.connected = False
            print("MQTT Connection failed")

    def execute(self):
        if not self.connected:
            self.led.on()
            return

        try:
            # Publish
            for sensor in self.sensors:
                name = sensor.name()
                topic = f"{self.topic_prefix}/{name}"
                payload = str(sensor.value())

                self.client.publish(topic, payload)
            # Read
            self.client.check_msg()
        except Exception as e:
            print(f"MQTT failure {e}, disconnecting")
            self.client.disconnect()
            self.connected = False
        self.led.switch()


    def incomming_message(self, b_topic, b_value):
        value = b_value.decode()
        topic = b_topic.decode()
        if topic == f"{self.topic_prefix}/set_mode" and (value == Regulator.AUTOMATIC or value == Regulator.MANUAL):
            self.regulator.set_mode(value)
        else:
            print(f"incorrect value: {value}")
        print(topic)
        print(value)

    def connect(self):
        try:
            self.client.connect()
            self.connected = True
        except Exception as e:
            print("MQTT Connection failed: ", e)
            self.connected = False

    def add_sensor(self, sensor):
        self.sensors.append(sensor)

    def disconnect(self):
        self.client.disconnect()
        self.connected = False
