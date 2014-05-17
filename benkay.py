#!/home/pi/.virtualenvs/benkaymeter/bin/python

import time
import datetime
import sys
import os
import threading

import nextbus
import runkeeper
import goodreads

import pwm_calibrate
import tlc5940
import gaugette.rotary_encoder

from settings import *

lock = threading.Lock()

class Thread(threading.Thread):
    def __init__(self, t, *args):
        threading.Thread.__init__(self, target=t, args=args)
        self.setDaemon(True)
        self.start()

def watch_mode(meter):
    """ Function that monitors the rotary encoder for input in a separate thread """
    encoder = gaugette.rotary_encoder.RotaryEncoder(ROTARYENCODERPIN_A, ROTARYENCODERPIN_B)    
    while True:
        # checks w/ default 4 detents per position
        delta = encoder.get_cycles()

        if delta!=0:
            old_mode = meter.current_mode
            meter.current_mode = (meter.current_mode + delta) % len(meter.MODES)
            if old_mode!=meter.current_mode:
                meter.set_leds_to_mode()
                meter.update_leds()
        
        # minimal sleep value to lower CPU load--checks @ 100Hz
        time.sleep(0.01)
     
class BenKayMeter(object):
    """ Measures things that Ben & Kay might like """
    
    MODES = ['NEXTBUS', 'GOODREADS', 'RUNKEEPER', 'BIKESHARE']

    def __init__(self):
        super(BenKayMeter, self).__init__()
    
        self.DEBUG = '--debug' in map(lambda x: x.lower().strip(), sys.argv)

        self.current_mode = 0
        self.leds = [[0,0,0]] * len(self.MODES)
        self.meter_value = 0

        if self.DEBUG:
            print 'Entering debug mode...'
        else:            
            self.meter_a = pwm_calibrate.PWMCalibrator(pin=METERPIN_A, calibration_file=CALIBRATION_FILE_A, smoothing=True)
            self.meter_a.load()
            self.meter_a.set(0)

            self.meter_b = pwm_calibrate.PWMCalibrator(pin=METERPIN_B, calibration_file=CALIBRATION_FILE_B, smoothing=True)
            self.meter_b.load()
            self.meter_b.set(0)        

            self.tlc = tlc5940.TLC5940(gsclkpin=GSCLKPIN, blankpin=BLANKPIN)
            self.tlc.writeAllDC(0)

            self.mode_thread = Thread(watch_mode, self)    

            self.set_leds_to_mode()
            self.update_leds()      

    def set_meter(self, value):
        # determine which GPIO is ground and which will add voltage
        if value>0:
            vcc_meter = self.meter_a
            ground_meter = self.meter_b
        else:
            vcc_meter = self.meter_b
            ground_meter = self.meter_a

        # are we going to zero? just adjust both, then; no harm
        if value==0:
            vcc_meter.set(0)
            ground_meter.set(0)

        # if the value currently zero? if so, no need to walk back
        elif self.meter_value==0:
            ground_meter.set(0)
            vcc_meter.set(abs(value))
        else:
            # are we staying on the same side of the meter?
            # if so, just adjust vcc
            same_direction = (((value/abs(value)) * (self.meter_value/abs(self.meter_value)))==1)
            if not same_direction:
                ground_meter.set(0)
            vcc_meter.set(abs(value))

        self.meter_value = value

    def set_leds_to_mode(self):
        """ Make the LED register reflect the current mode """
        self.leds = [[0,0,0]] * len(self.MODES)
        self.leds[self.current_mode] = [63, 63, 63]

    def update_leds(self):
        """ Shift contents of LED register into the TLC5940 """
        register = []
        for l in self.leds:
            for b in l:
                register.append(b)        
        
        # fill out register
        for i in range(len(register), self.tlc.numberof_leds-1):
            register.append(0)

        # correct for 1-pin offset of breakout board config
        register = [0] + register

        self.tlc.writeDC(register)

    def main(self):     

        nb = nextbus.NextbusPredictor(NEXTBUS_ROUTES)
        rk = runkeeper.RunKeeperInterface()
        gr = goodreads.GoodReadsInterface()
        bs = bikeshare.BikeShareInterface()

        while True:
            while self.mode==self.MODES.index('NEXTBUS'):                
                nb.refresh_if_necessary()

                # determine the number of predictions to display based on time of day and interval between
                num_predictions_to_display = 1
                predictions = (nb.get_nth_closest_arrival(0), nb.get_nth_closest_arrival(1))
                if not (None in predictions):
                    if (predictions[0][1] is not None) and (predictions[1][1] is not None): # do we have two valid predictions?
                        if predictions[0][1]<30: # is the next bus less than 30m away?
                            if predictions[1][1]<p_range[1]: # does the second one fit on the meter?
                                num_predictions_to_display = 2


                for pred in predictions[:num_predictions_to_display]:
                    if pred is None:
                        route = NEXTBUS_ROUTES[0]
                        minutes = None  
                    else:
                        (route, minutes) = pred

                    if minutes is None:
                        minutes = p_range[1]

                    minutes = min(max(minutes, p_range[0]), p_range[1])

                    if DEBUG:
                        print 'route is %s, arriving in %d minutes' % (route, minutes)
                    else:                        
                        p.setPWM(minutes)

                    time.sleep(3)                    


if __name__ == '__main__':
    try:
        b = BenKayMeter()

        #main()
    except Exception, e:
        f = open('/var/log/benkaymeter-crash.log', 'a')
        f.write(str(e))
        f.close()

        os.system('echo "%s" | mail -s "BEN/KAY METER CRASH LOG" thomas.j.lee@gmail.com' % str(e))

