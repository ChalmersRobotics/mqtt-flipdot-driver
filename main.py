import serial, yaml
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
            self.handle_action(self.displays[name], action, str(message.payload))
        else:
            logging.debug("Got message for unknown display '%s", name)


    def handle_action(self, display: DisplayBuffer, action, data):
        logging.debug("Handling '%s' with data '%s'", action, data)

        # only do basic text action for now
        if action != "text":
            return

        # format to look for: {X:Y:Font:Text goes here}
        # example: {0:0:SMALL:This is a lot if nice text :)}
        # multiple text pieces can be in the same message, just put them next to each other like so
        # "{0:0:SMALL:This is the first text}{0:10:SMALL:This is the second text!}

        # https://regexr.com/4dt6p
        texts = re.findall("{(\d+):(\d+):(\w+):(.+?)}", data)
        
        # if nothing was found, just use the raw text and some default font
        if not texts:
            logging.debug("No valid text format found, using raw payload instead")
            display.put_text(data, 0, 0)
        else:
            for text in texts:
                # make sure font exists
                if not hasattr(Font, text[2]):
                    logging.debug("Font '%s' not recognized", text[2])
                    continue
        
                display.put_text(text[3], x=int(text[0]), y=int(text[1]), font=Font[text[2]])


        # flush display data
        buffer = display.finalize_buffer()
        logging.debug("Sending %s", buffer)
        self.port.write(buffer)



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