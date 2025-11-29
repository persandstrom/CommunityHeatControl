from regulator import Regulator
from umqtt.simple import MQTTClient


class MQTTController:
    def __init__(self, mqtt_settings, system):
        self.client = MQTTClient(
            client_id=mqtt_settings["client_id"],
            server=mqtt_settings["broker"],
            user=mqtt_settings["user"],
            password=mqtt_settings["password"])
        self.system = system

        self.topic_prefix = mqtt_settings["topic_prefix"]
        self.connected = False

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

    def disconnect(self):
        self.client.disconnect()
        self.connected = False


    def execute(self):
        if not self.connected:
            return

        try:
            self.client.publish(
                f"{self.topic_prefix}/pump_status",
                str(self.system.pump.status))
            self.client.publish(
                f"{self.topic_prefix}/pump_power",
                str(self.system.pump.power))
            self.client.publish(
                f"{self.topic_prefix}/valve_position",
                str(self.system.valve.position))
            self.client.publish(
                f"{self.topic_prefix}/regulator_mode",
                str(self.system.regulator.mode))
            self.client.publish(
                f"{self.topic_prefix}/regulation_adjustment",
                str(self.system.regulator.regulation_adjustment))
            self.client.publish(
                f"{self.topic_prefix}/curve_gain",
                str(self.system.regulator.gain))
            self.client.publish(
                f"{self.topic_prefix}/offset",
                str(self.system.regulator.offset))
            self.client.publish(
                f"{self.topic_prefix}/proportional_gain",
                str(self.system.regulator.proportional_gain))
            self.client.publish(
                f"{self.topic_prefix}/adjustment_threshold",
                str(self.system.regulator.adjustment_threshold))
            self.client.publish(
                f"{self.topic_prefix}/ambient_temp",
                str(self.system.ambient_temp.value))
            self.client.publish(
                f"{self.topic_prefix}/primary_supply_temp",
                str(self.system.primary_supply_temp.value))
            self.client.publish(
                f"{self.topic_prefix}/primary_return_temp",
                str(self.system.primary_return_temp.value))
            self.client.publish(
                f"{self.topic_prefix}/secondary_supply_temp",
                str(self.system.secondary_supply_temp.value))
            self.client.publish(
                f"{self.topic_prefix}/secondary_return_temp",
                str(self.system.secondary_return_temp.value))
            self.client.check_msg()
        except Exception as e:
            print(f"MQTT failure {e}, disconnecting")
            self.client.disconnect()
            self.connected = False

    def incomming_message(self, b_topic, b_value):
        value = b_value.decode()
        topic = b_topic.decode()
        if ( topic == f"{self.topic_prefix}/set_mode"
             and (value == Regulator.AUTOMATIC or value == Regulator.MANUAL)):
            self.system.regulator.set_mode(value)
        else:
            print(f"incorrect value: {value}")
