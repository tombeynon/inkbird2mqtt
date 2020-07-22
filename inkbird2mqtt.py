#!/usr/bin/env python3

import datetime
import logging
import json
from bluepy import btle
import paho.mqtt.client as mqtt

logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.DEBUG,
        datefmt='%Y-%m-%d %H:%M:%S')

from inkbird2mqtt_config import (
    mac,
    mqtt_host,
    mqtt_port,
    mqtt_user,
    mqtt_pass,
    mqtt_client,
    mqtt_topic,
)


def float_value(nums):
    num = nums[1] * 256 + nums[0]
    # check if temp is negative
    if num >= 0x8000:
        num = num - 0x10000
    return float(num) / 100

def get_readings():
    try:
        dev = btle.Peripheral(mac, addrType=btle.ADDR_TYPE_PUBLIC)
        readings = dev.readCharacteristic(0x28)
        return readings
    except Exception as e:
        logging.error("Error reading BTLE: {}".format(e))
        return False


def run():
    readings = get_readings()

    if not readings:
        logging.debug("No data: {}".format(readings))
        return

    logging.debug("raw data: {}".format(readings))

    # little endian, first two bytes are temp_c, second two bytes are humidity
    temperature_c = float_value(readings[0:2])
    humidity = float_value(readings[2:4])
    sensor = 'internal' if readings[4] == 0 else 'external' if readings[4] == 1 else 'unknown'
    # battery = readings[7]

    # Get current time
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Print info to terminal
    logging.info("\n" + mac + " @ " + str(time))
    logging.info("  Temp: " + str(temperature_c) + "\u00B0c")
    logging.info("  Humidity: " + str(humidity) + "%")
    logging.info("  Sensor: " + str(sensor))
    # logging.info("  Battery: " + str(battery))

    data = {}
    data['time'] = time
    data['temperature'] = temperature_c
    data['humidity'] = humidity
    data['sensor'] = sensor

    msg_data = json.dumps(data)

    print(
        "\n  Publishing MQTT payload to "
        + mqtt_topic
        + mac
        + " ...\n\n    "
        + msg_data
    )
    mqttc = mqtt.Client(mqtt_client)
    mqttc.username_pw_set(mqtt_user, mqtt_pass)
    mqttc.connect(mqtt_host, mqtt_port)
    mqttc.publish(mqtt_topic + mac, msg_data, 1)

run()
