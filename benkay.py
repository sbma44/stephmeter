#!/home/pi/.virtualenvs/benkay/bin/python

import time
import datetime
import sys
import os
import threading

import nextbus
import runkeeper
import goodreads

import pwm_calibrate
import gaugette.rotary_encoder

from settings import *

lock = threading.Lock()

class Thread(threading.Thread):
    def __init__(self, t, *args):
        threading.Thread.__init__(self, target=t, args=args)
        self.start()

def watch_mode(meter):
    with lock:
        meter.check_mode()
        time.sleep(0.01)

def set_led(meter):
    with lock:
        meter.set_led()
        time.sleep(0.02)


class BenKayMeter(object):
    """ Measures things that Ben & Kay might like """
    
    MODES = ['NEXTBUS', 'GOODREADS', 'RUNKEEPER', 'BIKESHARE']

    def __init__(self):
        super(BenKayMeter, self).__init__()
    
        self.DEBUG = '--debug' in map(lambda x: x.lower().strip(), sys.argv)

        if self.DEBUG:
            print 'Entering debug mode...'
        else:            
            self.p = pwm_calibrate.PWMCalibrator(calibration_file=CALIBRATION_FILE, smoothing=True)
            self.p.load()
            self.p_range = p.get_range()

            self.encoder_worker = gaugette.rotary_encoder.RotaryEncoder.Worker(ROTARY_ENCODER_PINS[0], ROTARY_ENCODER_PINS[1])
            self.encoder_worker.start()

            self.led_thread = Thread(set_led, self)
            self.mode_thread = Thread(watch_mode, self)    

        self.current_mode = 0
        
    def check_mode(self):
        turns = self.encoder_worker.encoder.get_cycles()
        self.current_mode = (self.current_mode + turns) % len(self.MODES)    

    def set_led(self):
        pass

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
        main()
    except Exception, e:
        f = open('/var/log/stephmeter-crash.log', 'a')
        f.write(str(e))
        f.close()

        os.system('echo "%s" | mail -s "STEPHMETER CRASH LOG" thomas.j.lee@gmail.com' % str(e))

