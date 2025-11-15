# CommunityHeatControl
Control/monitor my community heating system




## Circuit

![alt text](circuit.png "Title")



## Settings

The `settings.json` file contains the configuration parameters for the ESP32-based heating control system. Create this file in the root directory with your specific values.

### Configuration Structure

The settings file is structured with four main sections:

#### 1. Station (WiFi Client) Configuration
Configures the ESP32 to connect to an existing WiFi network as a client.
- **ssid**: The name of your WiFi network
- **password**: The WiFi network password


#### 2. Access Point Configuration
Configures the ESP32 to create its own WiFi hotspot for direct access. Used by Shelly plug and direct access if not connected to WiFi.
- **ssid**: The network name that devices can connect to directly
- **password**: Password for connecting to the ESP32's hotspot


#### 3. MQTT Configuration
Enables communication with an MQTT broker for remote monitoring and control.
- **client_id**: Unique identifier for this device on the MQTT network
- **broker**: IP address of the MQTT broker server
- **user/password**: Credentials for authenticating with the MQTT broker


#### 4. Web Server Configuration
Configures the built-in web interface.
- **port**: TCP port number for accessing the web control panel

### Example Configuration

```json
{
    "station": {
        "ssid": "YourWiFiNetwork",
        "password": "your_wifi_password"
    },
    "access_point": {
        "ssid": "HeatController",
        "password": "your_ap_password"
    },
    "mqtt": {
        "client_id": "heat-controller",
        "broker": "192.168.1.100",
        "user": "mqtt_username",
        "password": "mqtt_password"
    },
    "web_server": {
        "port": 80
    }
}
```
