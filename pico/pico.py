# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-w-mqtt-micropython/

from machine import Pin, unique_id
from time import sleep
import network
from umqtt.simple import MQTTClient
import ujson
import config

# Define LED
led = Pin('LED', Pin.OUT)

# Constants for MQTT Topics
MQTT_TOPIC_LED = 'pico/led'

# MQTT Parameters
MQTT_SERVER = config.mqtt_server
MQTT_PORT = 0
MQTT_USER = config.mqtt_username
MQTT_PASSWORD = config.mqtt_password
MQTT_CLIENT_ID = b'raspberrypi_picow'
MQTT_KEEPALIVE = 7200
MQTT_SSL = False   # set to False if using local Mosquitto MQTT broker
MQTT_SSL_PARAMS = {'server_hostname': MQTT_SERVER}


CMD_TOPIC = f"{MQTT_TOPIC_LED}/set"
STATE_TOPIC = f"{MQTT_TOPIC_LED}/state"

# Init Wi-Fi Interface
def initialize_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # Connect to the network
    wlan.connect(ssid, password)

    # Wait for Wi-Fi connection
    connection_timeout = 10
    while connection_timeout > 0:
        if wlan.status() >= 3:
            break
        connection_timeout -= 1
        print('Waiting for Wi-Fi connection...')
        sleep(1)

    # Check if connection is successful
    if wlan.status() != 3:
        return False
    else:
        print('Connection successful!')
        network_info = wlan.ifconfig()
        print('IP address:', network_info[0])
        return True

# Connect to MQTT Broker
def connect_mqtt():
    try:
        client = MQTTClient(client_id=MQTT_CLIENT_ID,
                            server=MQTT_SERVER,
                            port=MQTT_PORT,
                            user=MQTT_USER,
                            password=MQTT_PASSWORD,
                            keepalive=MQTT_KEEPALIVE,
                            ssl=MQTT_SSL,
                            ssl_params=MQTT_SSL_PARAMS)
        client.connect()
        return client
    except Exception as e:
        print('Error connecting to MQTT:', e)

# Subcribe to MQTT topics
def subscribe(client, topic):
    client.subscribe(topic)
    print('Subscribe to topic:', topic)

def getId():
    id = unique_id()
    stringId = ""
    for b in id:
        stringId += hex(b)[2:]
    return stringId

# Function to publish Home Assistant MQTT Discovery messages
def publish_discovery():
    pico_unique_id = getId()
    switch_id = f"sw_{pico_unique_id}"

    payload = {
        "dev": {
            "ids": pico_unique_id,
            "name": "Pico MQTT Switch",
#             "mf": "Wechant Loup",
#             "mdl": "pico_mqtt_switch",
#             "sw": "1.0",
#             "sn": pico_unique_id,
#             "hw": "1.0",
          },
          "o": {
            "name":"pico_mqtt_switch",
            "sw": "0.1",
            "url": "https://github.com/Pilou44/mqttSwitch",
          },
          "~": MQTT_TOPIC_LED,
          "device_class": "device_class",
          "unique_id": switch_id,
          "cmd_t": "~/set",
          "stat_t": "~/state",
#           "qos": 2,
        #"name": f"Pico {sensor_name}",
        #"unique_id": unique_id,
        #"state_topic": state_topic,
        #"unit_of_measurement": unit,
        #"availability": {
        #    "topic": availability_topic
        #}
    }
    
    # Convert payload to JSON string for publishing
    payload_json = ujson.dumps(payload)

    # Print the payload for debugging
    print(f"Publishing : {payload_json}")
    
    conf_topic = f"{MQTT_TOPIC_LED}/config"
    client.publish(MQTT_TOPIC_LED, ujson.dumps(payload), retain=True)

# Callback function that runs when you receive a message on subscribed topic
def my_callback(topic, message):
    # Perform desired actions based on the subscribed topic and response
    print('Received message on topic:', topic)
    print('Response:', message)
    # Check the content of the received message
    
    if message == b'ON':
        print('Turning LED ON')
        led.value(1)  # Turn LED ON
    elif message == b'OFF':
        print('Turning LED OFF')
        led.value(0)  # Turn LED OFF
    else:
         print('Unknown command')
#     if topic == CMD_TOPIC:
#         if message == b'ON':
#             print('Turning LED ON')
#             led.value(1)  # Turn LED ON
#         elif message == b'OFF':
#             print('Turning LED OFF')
#             led.value(0)  # Turn LED OFF
#         else:
#             print('Unknown command')
#     elif topic == STATE_TOPIC:
#         print('State topic')
#     else:
#         print(f"Unknown topic {topic}")
    
try:
    # Initialize Wi-Fi
    if not initialize_wifi(config.wifi_ssid, config.wifi_password):
        print('Error connecting to the network... exiting program')
    else:
        # Connect to MQTT broker, start MQTT client
        client = connect_mqtt()
        publish_discovery()
        client.set_callback(my_callback)
        
        subscribe(client, CMD_TOPIC)
        subscribe(client, STATE_TOPIC)
        
        # Continuously checking for messages
        while True:
            sleep(5)
            client.check_msg()
            print('Loop running')
except Exception as e:
    print('Error:', e)
