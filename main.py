import serial, yaml, json
import io, signal
import time, datetime
import logging
import re

import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe

from display import DisplayBuffer, Font

# config file to load
config_filename = "config.yaml"

class MQTTDriver:
    def __init__(self, config):
        self.config = config
        self.port = None
        self.mqttClient = None
        self.displays = {}


    def run(self):
        # register sigint handler
        signal.signal(signal.SIGINT, self.handle_sigint)

        driver_cfg = self.config['driver']

        # try to open the serial port
        portname = driver_cfg['port'] or 'loop://'
        logging.info("Opening serial port '%s' ...", portname)
        self.port = serial.serial_for_url(portname, baudrate=driver_cfg['baudrate'])

        # iterate through each configured display and create a DisplayBuffer for each one of them
        for disp in driver_cfg['display']:        
            self.displays[disp['name']] = DisplayBuffer(disp['address'], disp['width'], disp['height'])
        
        # connect to mqtt and let it do its thing
        self.mqtt_connect()
        self.mqttClient.loop_forever()

        # disconnect was called, close port
        logging.info("MQTT loop exited, closing port ...")

        self.port.close()

        logging.info("Bye!")

    def handle_sigint(self, signal, frame):
        logging.info("Caught SIGINT, stopping...")

        if self.mqttClient:
            self.mqttClient.disconnect()

    def mqtt_connect(self):
        logging.info("Setting up MQTT...")

        # create client
        self.mqttClient = mqtt.Client(self.config['mqtt']['id'])
        
        # setup callback(s)
        self.mqttClient.on_connect = self.on_connect
        self.mqttClient.on_disconnect = self.on_disconnect
        self.mqttClient.on_message = self.on_message

        # load broker config
        broker = self.config['mqtt']['broker']
        
        # check to see if username and password is set
        if('username' in broker and 'password' in broker):
            logging.info("Using MQTT authentication")
            # set username and password for MQTT client
            self.mqttClient.username_pw_set(broker['username'], broker['password'])

        # connect
        logging.info("Connecting to broker @ %s:%s ...", broker['host'], broker['port'])
        self.mqttClient.connect(broker['host'], port=broker['port'])

        logging.info("Connection successfull")

    # MQTT callback(s)
    def on_connect(self, client, userdata, flags, rc):
        logging.debug("MQTT connected (code=%s) ", rc)

        # subscribe to the configured topic and all its subtopics
        client.subscribe(self.config['mqtt']['base_topic']+"/#")

    def on_disconnect(self, client, userdata, rc):
        logging.debug("MQTT disconnected (code=%s)", rc) 

    def on_message(self, client, userdata, message):
        try:
            self.parse_message(message)
        except Exception as e:
            logging.exception(e)

    def parse_message(self, message):
        # parse what display to use and what action to do
        m = re.search("flipdot\/(\w+)\/(\w+)", message.topic)
        
        # no match?
        if not m:
            logging.debug("Got message on unrecognized topic '%s' with payload '%s", message.topic, message.payload)
            return

        # get matches
        name = m.group(1)
        action = m.group(2)

        # check that the chosen device exist
        if name in self.displays:
            self.handle_action(self.displays[name], action, message.payload.decode("utf-8"))
        else:
            logging.debug("Got message for unknown display '%s", name)


    def handle_action(self, display: DisplayBuffer, action, data):
        logging.debug("Handling '%s' with data '%s'", action, data)

        # only do basic text action for now
        if action != "text":
            return
        
        # format is a simple JSON array of objects of the form:
        # {
        #   "font": "F64",
        #   "x": 0,
        #   "y": 0,
        #   "text": "Text to display here!"
        # }
        # both font, x and y are optional and have the default values "SMALL_F" , 0 and 0 respectively

        
        try:
            # parse data as JSON, assuming its an array of objects
            parts_list = json.loads(data)

            # write all text parts to the screen with default values for the unspecified information
            for string in parts_list:
                display.put_text(
                    self.text_convert(string.get('text', "?")), 
                    x=string.get('x', 0), 
                    y=string.get('y', 0), 
                    font=getattr(Font, string.get('font', ""), Font.SMALL_F)
                )

        except json.decoder.JSONDecodeError as e:
            logging.debug("There was an error while parsing data as JSON, using raw payload instead: " + str(e))
            display.put_text(self.text_convert(data), 0, 0)            

        # flush display data
        buffer = display.finalize_buffer()
        logging.debug("Sending %s", buffer)
        self.port.write(buffer)

    def text_convert(self, text:str) -> str:
        # converts special characters like ÅÄÖ and åäö to what the display expects
        for (o, r) in [('å', '}'), ('ä', '{'), ('ö', '|'),('Å', ']'), ('Ä', '['), ('Ö', '\\')]:
            text = text.replace(o, r)
        
        return text

 

def main():
    # initialize logger
    logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] %(levelname)s %(message)s')#, datefmt='%Y-%m-%d %H:%M:%S')

    # read config file
    logging.info("Using config file " + config_filename)
    with open(config_filename, 'r') as f:
        cfg = yaml.load(f, Loader=yaml.SafeLoader)

    # let driver do its thing    
    driver = MQTTDriver(cfg)
    driver.run()
            
if __name__ == "__main__":
    main()