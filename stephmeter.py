import pwm_calibrate
import led
import paho.mqtt.client as mqtt

from settings import *

if __name__ == '__main__':
    l = led.LED(SERIAL_DEVICE, SERIAL_SPEED)
    p = pwm_calibrate.PWMCalibrator(calibration_file=CALIBRATION_FILE, smoothing=True)
    p.load()
    p_range = p.get_range()

    p.setPWM(p_range[0])

    def on_connect(client, userdata, flags, rc):
        print('connected to MQTT server')
        client.subscribe(MQTT_TOPIC_PWM)
        client.subscribe(MQTT_TOPIC_LED)

    def on_message(client, userdata, message):
        print("%s %s" % (message.topic, message.payload))
        if message.topic == MQTT_TOPIC_PWM:
            p = userdata['pwm']
            val = max(p_range[0], min(p_range[1], int(message.payload)))
            p.setPWM(val)
        elif message.topic == MQTT_TOPIC_LED:
            l = userdata['led']
            l.set(message.payload[0], message.payload[1], message.payload[2])

    mqtt_client = mqtt.Client('stephmeter', userdata={'pwm': p, 'led': l})
    mqtt_client.on_message = on_message
    mqtt_client.on_connect = on_connect
    mqtt_client.connect(MQTT_SERVER, MQTT_PORT, 60)
    mqtt_client.loop_forever()
