# Rui Santos & Sara Santos - Random Nerd Tutorials
# Complete project details at https://RandomNerdTutorials.com/raspberry-pi-pico-w-mqtt-micropython/

from machine import Pin
from time import sleep_ms, ticks_ms, ticks_diff
from umqtt.simple import MQTTClient
import ujson
import config
from core import getId, initialize_wifi

from neopixel import NeoPixel
from led_modes import snes, ps1, wiiu, nes, n64

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
    global enabled
    # Perform desired actions based on the subscribed topic and response
    print('Received message on topic:', topic)
    print('Response:', message)
    # Check the content of the received message
    
    if message == b'ON':
        print('Turning ON')
        enabled = True
        led.value(1)  # Turn LED ON
        switch_on(pixels0, wiiu)
        switch_on(pixels1, n64)
        switch_on(pixels2, snes)
        switch_on(pixels3, nes)
        client.publish(STATE_TOPIC, "ON")
    elif message == b'OFF':
        print('Turning OFF')
        enabled = False
        led.value(0)  # Turn LED OFF
        switch_off_all()
        client.publish(STATE_TOPIC, "OFF")
    else:
         print('Unknown command')

enabled = False
numpix = 12
pin0 = Pin(28, Pin.OUT)
pixels0 = NeoPixel(pin0, numpix)
pin1 = Pin(27, Pin.OUT)
pixels1 = NeoPixel(pin1, numpix)
pin2 = Pin(26, Pin.OUT)
pixels2 = NeoPixel(pin2, numpix)
pin3 = Pin(22, Pin.OUT)
pixels3 = NeoPixel(pin3, numpix)

def switch_on(pixels, mode):
    n = pixels.n
    for i in range(n):
        pixels[i] = mode[i]
    pixels.write()

def switch_off_all():
    switch_off(pixels0)
    switch_off(pixels1)
    switch_off(pixels2)
    switch_off(pixels3)

def switch_off(pixels):
    global enabled
    n = pixels.n
    for i in range(n):
        pixels[i] = (0, 0, 0)
    pixels.write()
    
def rotate(pixels):
    n = pixels.n
    r0, g0, b0 = pixels[0]
    for i in range(n - 1):
        pixels[i] = pixels[i + 1]
    pixels[n - 1] = (r0, g0, b0)
    pixels.write()

def run():
    global client
    global enabled
    # Initialize Wi-Fi
    if not initialize_wifi(config.wifi_ssid, config.wifi_password):
        print('Error connecting to the network... exiting program')
    else:
        # Connect to MQTT broker, start MQTT client
        client = connect_mqtt()
        publish_discovery()
        if enabled:
            client.publish(STATE_TOPIC, "ON")
        else:
            client.publish(STATE_TOPIC, "OFF")
        client.set_callback(my_callback)
        
        client.subscribe(CMD_TOPIC)
        
        # Continuously checking for messages
        while True:
            start = ticks_ms()
            client.check_msg()
            if enabled:
                rotate(pixels0)
                rotate(pixels1)
                rotate(pixels2)
                rotate(pixels3)
                sleep_time_ms = 75
            else:
                sleep_time_ms = 1000
            diff = ticks_diff(ticks_ms(), start)
            sleep_time = sleep_time_ms - diff
            sleep_ms(sleep_time)

while True:
    try:
        print('Run')
        run()
    except KeyboardInterrupt:
        switch_off_all()
        machine.reset()
    except Exception as e:
        print('Exception')
        print(e)
        pass
