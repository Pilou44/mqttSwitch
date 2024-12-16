# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-w-mqtt-micropython/

from machine import Pin
from time import sleep, sleep_ms
from umqtt.simple import MQTTClient
import ujson
import config
from core import getId, initialize_wifi

from neopixel import NeoPixel
import _thread

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
    payload = {
        "name": "Pico LED",
        "unique_id": UNIQUE_ID,
        "command_topic": CMD_TOPIC,
        "state_topic": STATE_TOPIC,
        "payload_on": "ON",
        "payload_off": "OFF",
#         "retain": "false",
        "device": {
            "manufacturer": "Wechant Loup",
            "model": "Pico LED",
            "identifiers": UNIQUE_ID,
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
        switch_on()
        client.publish(STATE_TOPIC, "ON")
    elif message == b'OFF':
        print('Turning LED OFF')
        led.value(0)  # Turn LED OFF
        switch_off()
        client.publish(STATE_TOPIC, "OFF")
    else:
         print('Unknown command')

enabled = False
numpix = 12
pin = Pin(28, Pin.OUT)
pixels = NeoPixel(pin, numpix)

def switch_on():
    enabled = True
    pixels[0] = (255, 0, 0) # set to red, full brightness
    pixels[1] = (0, 128, 0) # set to green, half brightness
    pixels[2] = (0, 0, 64)  # set to blue, quarter brightness
    pixels.write()
    print("Launch thread")
    _thread.start_new_thread(thread_loop, ())
        
def thread_loop():
    print("Thread started")
    global enabled
    print(f"Emabled = {enabled}")
    enabled = True
    print(f"Emabled = {enabled}")
    while (enabled):
        sleep_ms(500)
        rotate(pixels)
    print("Thread ended")

def switch_off():
    global enabled
    print("Switch off")
    enabled = False
    print(f"Emabled = {enabled}")
    pixels[0] = (0, 0, 0)
    pixels[1] = (0, 0, 0)
    pixels[2] = (0, 0, 0)
    pixels.write()
    
def rotate(np):
    n = np.n
    r, g, b = np[0]
    for i in range(n - 1):
        np[i] = np[i + 1]
    np[n - 1] = (r, g, b)
    np.write()

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
        switch_off()
        machine.reset()
    except Exception as e:
        switch_off()
        print(e)
        pass
