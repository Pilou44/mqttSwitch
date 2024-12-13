# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-w-mqtt-micropython/

from machine import Pin
from time import sleep
from umqtt.simple import MQTTClient
import ujson
import config
from core import getId, initialize_wifi

# Define LED
led = Pin('LED', Pin.OUT)

UNIQUE_ID = getId()
# Constants for MQTT Topics
MQTT_TOPIC_LED = f"switch/wechantloup/{UNIQUE_ID}"

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

# Function to publish Home Assistant MQTT Discovery messages
def publish_discovery():
    pico_unique_id = getId()
    switch_id = f"sw_{pico_unique_id}"

    payload = {
        "name": "Pico LED",
        "unique_id": pico_unique_id,
        "command_topic": CMD_TOPIC,
        "state_topic": STATE_TOPIC,
        "payload_on": "ON",
        "payload_off": "OFF",
#         "retain": "false",
        "device": {
            "manufacturer": "Wechant Loup",
            "model": "Pico LED",
            "identifiers": pico_unique_id,
        },
    }
    
    # Convert payload to JSON string for publishing
    payload_json = ujson.dumps(payload)
    
    conf_topic = f"homeassistant/{MQTT_TOPIC_LED}/config"
    
    # Print the payload for debugging
    print(f"Publishing to {conf_topic}: {payload_json}")
    
    client.publish(conf_topic, ujson.dumps(payload), retain=True)

# Callback function that runs when you receive a message on subscribed topic
def my_callback(topic, message):
    # Perform desired actions based on the subscribed topic and response
    print('Received message on topic:', topic)
    print('Response:', message)
    # Check the content of the received message
    
    if message == b'ON':
        print('Turning LED ON')
        led.value(1)  # Turn LED ON
        client.publish(STATE_TOPIC, "ON")
    elif message == b'OFF':
        print('Turning LED OFF')
        led.value(0)  # Turn LED OFF
        client.publish(STATE_TOPIC, "OFF")
    else:
         print('Unknown command')


def run():
    global client
    # Initialize Wi-Fi
    if not initialize_wifi(config.wifi_ssid, config.wifi_password):
        print('Error connecting to the network... exiting program')
    else:
        # Connect to MQTT broker, start MQTT client
        client = connect_mqtt()
        publish_discovery()
        client.set_callback(my_callback)
        
        client.subscribe(CMD_TOPIC)
        
        # Continuously checking for messages
        while True:
            sleep(1)
            client.check_msg()
            print('Loop running')

while True:
    try:
        print('Run')
        run()
    except KeyboardInterrupt:
        machine.reset()
    except Exception as e:
        print(e)
        pass
