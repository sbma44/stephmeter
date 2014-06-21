#!/home/pi/.virtualenvs/benkaymeter/bin/python

#pylint: disable=C0301

import time
import datetime
import sys
import os
import threading

import nextbus
import runkeeper
import goodreads
import bikeshare

import pwm_calibrate
import tlc5940
import gaugette.rotary_encoder

from settings import *

lock = threading.Lock()

class Thread(threading.Thread):
    """ Convenience method for process threads """
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

        if delta != 0:
            with lock:
                old_mode = meter.current_mode
                meter.current_mode = (meter.current_mode + delta) % len(meter.MODES)
                if old_mode != meter.current_mode:
                    meter.set_color()
                    meter.set_leds_to_mode()
                    meter.update_leds()
        
        # minimal sleep value to lower CPU load--checks @ 100Hz
        time.sleep(0.01)

def manage_leds(meter):
    """ Thread that manages LED state / enables blinking """    
    while True:
        if meter.blinking:
            with lock:
                meter.leds_backup_state = list(meter.leds)
                if (time.time() % 1) > 0.5:
                    meter.leds = [[0, 0, 0]] * len(meter.MODES)
                else:
                    meter.leds = list(meter.led_backup_state)
                meter.update_leds()
        time.sleep(0.01)

class BenKayMeter(object):
    """ Measures things that Ben & Kay might like """
    
    MODES = ['NEXTBUS', 'GOODREADS', 'RUNKEEPER', 'BIKESHARE']

    def __init__(self):
        super(BenKayMeter, self).__init__()
    
        self.DEBUG = '--debug' in map(lambda x: x.lower().strip(), sys.argv)

        self.current_mode = 0
        self.leds = [[0, 0, 0]] * len(self.MODES)
        self.set_color()
        self.meter_value = 0

        self.blinking = False

        if self.DEBUG:
            print 'Entering debug mode...'
        
        self.meter_a = pwm_calibrate.PWMCalibrator(pin=METERPIN_A, calibration_file=CALIBRATION_FILE_A, smoothing=True)
        self.meter_a.load()
        self.meter_a.set(0)

        self.meter_b = pwm_calibrate.PWMCalibrator(pin=METERPIN_B, calibration_file=CALIBRATION_FILE_B, smoothing=True)
        self.meter_b.load()
        self.meter_b.set(0)        

        self.tlc = tlc5940.TLC5940(gsclkpin=GSCLKPIN, blankpin=BLANKPIN)
        self.tlc.writeAllDC(0)

        self.mode_thread = Thread(watch_mode, self)   
        self.led_thread = Thread(manage_leds, self) 

        self.set_leds_to_mode()
        self.update_leds()      

    def start_blinking(self):
        self.led_backup_state = list(self.leds)
        self.blinking = True

    def stop_blinking(self):
        self.blinking = False

    def set_meter(self, value):
        """ Sets VU meter within [-25, 25] range """

        # determine which GPIO is ground and which will add voltage
        if value > 0:
            vcc_meter = self.meter_a
            ground_meter = self.meter_b
        else:
            vcc_meter = self.meter_b
            ground_meter = self.meter_a

        # are we going to zero? just adjust both, then; no harm
        if value == 0:
            vcc_meter.set(0)
            ground_meter.set(0)

        # if the value currently zero? if so, no need to walk back
        elif self.meter_value == 0:
            ground_meter.set(0)
            vcc_meter.set(abs(value))
        else:
            # are we staying on the same side of the meter?
            # if so, just adjust vcc
            same_direction = ((value / abs(value)) * (self.meter_value / abs(self.meter_value))) == 1
            if not same_direction:
                ground_meter.set(0)
            vcc_meter.set(abs(value))

        self.meter_value = value

    def set_leds_to_mode(self):
        """ Make the LED register reflect the current mode """
        self.leds = [[0, 0, 0]] * len(self.MODES)
        self.leds[self.current_mode] = list(self.color)
        # print 'just set LEDs to color %s' % str(self.color)

    def update_leds(self):
        """ Shift contents of LED register into the TLC5940 """
        register = []
        for led in self.leds:
            for brightness in led:
                register.append(brightness)        
        
        # fill out register
        for padding_i in range(len(register), self.tlc.numberof_leds-1):
            register.append(0)

        # correct for 1-pin offset of breakout board config
        register = [0] + register

        self.tlc.writeDC(register)

        # print 'updated leds'

    def set_color(self, color=[63, 63, 63]):
        self.color = list(color)

    def sleep_until_input(self, delay):
        """ Sleep for delay seconds, but break if a mode change 
            Returns true if delay completed, false if not """
        start_time = time.time()
        start_mode = self.current_mode
        while time.time() < (start_time + delay):
            if self.current_mode != start_mode:
                return False
            time.sleep(0.01)
        return True


    def main(self): 
        """ Primary loop """    

        nb = nextbus.NextbusPredictor(NEXTBUS_ROUTES)
        rk = runkeeper.RunKeeperInterface()
        gr = goodreads.GoodReadsInterface()
        bs = bikeshare.BikeShareInterface(BIKESHARE_XML_URL, BIKESHARE_STATION_IDS)

        while True:

            newly_in_mode = True
            self.set_meter(0)
            self.set_color()
            self.update_leds()

            while self.current_mode == self.MODES.index('BIKESHARE'):                

                if self.DEBUG:
                    print str(datetime.datetime.now()), 'bikeshare mode'

                if newly_in_mode:
                    self.set_meter(0)
                    self.set_color()
                    self.update_leds() 

                    maintain_mode = self.sleep_until_input(1)
                    if not maintain_mode:
                        break
                                       
                    self.start_blinking()                    
                
                bs.refresh()

                if newly_in_mode:
                    self.stop_blinking()
                    newly_in_mode = False

                maintain_mode = True
                start_time = time.time()
                while time.time() < (start_time + BIKESHARE_REFRESH_RATE) and maintain_mode:

                    # set LED color
                    bike_sum = 0
                    for station in bs.bike_availability:
                        bike_sum = bike_sum + bs.bike_availability[station].get('bikes', 0)
                    
                    with lock:
                        # plenty of bikes!
                        if bike_sum > 5:
                            self.set_color([0, 63, 0])                            
                        # not so many bikes
                        elif bike_sum > 0:
                            self.set_color([63, 63, 0])
                        # no bikes :-(
                        else:
                            self.set_color([63, 0, 0])
                        self.set_leds_to_mode()
                        self.update_leds()

                    for (station_index, multiplier) in enumerate((-1, 1)):                        
                        num_bikes = bs.bike_availability[BIKESHARE_STATION_IDS[station_index]].get('bikes', 0)                    
                        self.set_meter(multiplier * num_bikes)                        

                        # sleep, but allow breaks
                        maintain_mode = self.sleep_until_input(5)
                        if not maintain_mode:
                            break

            if not newly_in_mode:
                continue

            while self.current_mode == self.MODES.index('RUNKEEPER'):                

                if self.DEBUG:
                    print str(datetime.datetime.now()), 'runkeeper mode'

                if newly_in_mode:
                    self.set_meter(0)
                    self.set_color()
                    self.update_leds() 

                    maintain_mode = self.sleep_until_input(1)
                    if not maintain_mode:
                        break

                    self.start_blinking()                    
                
                rk.refresh_all()

                if newly_in_mode:
                    self.stop_blinking()
                    newly_in_mode = False

                start_time = time.time()
                maintain_mode = True
                while time.time() < (start_time + RUNKEEPER_REFRESH_RATE) and maintain_mode:

                    # cycle through every available token's runkeeper mileage
                    for (i, rkt) in enumerate(rk.tokens.keys()):
                        miles = rk.calculate_mileage(rkt)
                        self.set_meter((1, -1)[i % 2] * miles)                        

                        # sleep, but allow breaks
                        maintain_mode = self.sleep_until_input(5)
                        if not maintain_mode:
                            break

            if not newly_in_mode:
                continue

            while self.current_mode == self.MODES.index('NEXTBUS'):   
                
                if self.DEBUG:
                    print str(datetime.datetime.now()), 'nextbus mode'

                if newly_in_mode:
                    self.set_meter(0)
                    self.set_color()
                    self.update_leds()
                    
                    maintain_mode = self.sleep_until_input(1)
                    if not maintain_mode:
                        break

                    self.start_blinking()
                    nb.refresh_all()
                    

                else:
                    nb.refresh_if_necessary()

                if newly_in_mode:
                    self.stop_blinking()
                    newly_in_mode = False

                # determine the number of predictions to display based on time of day and interval between
                num_predictions_to_display = 1
                predictions = (nb.get_nth_closest_arrival(0), nb.get_nth_closest_arrival(1))
                if not None in predictions:
                    if (predictions[0][1] is not None) and (predictions[1][1] is not None): # do we have two valid predictions?
                        if predictions[0][1] < 30: # is the next bus less than 30m away?
                            if predictions[1][1] < METER_MAX_VALUE: # does the second one fit on the meter?
                                num_predictions_to_display = 2

                nearest_prediction = 999
                for i in range(0, num_predictions_to_display):
                    nearest_prediction = min(nearest_prediction, predictions[i][1])

                # set LEDs
                with lock:
                    # there's no time! RED
                    if nearest_prediction < 1:
                        self.set_color([63, 0, 0])                            
                    # you should maybe get going YELLOW
                    elif nearest_prediction < 3:
                        self.set_color([63, 63, 0])
                    # plenty of time! GREEN
                    else:
                        self.set_color([0, 63, 0])
                    self.set_leds_to_mode()
                    self.update_leds()

                # set meter
                for (prediction_index, multiplier) in enumerate((1, -1)[:num_predictions_to_display]):                    
                    minutes_until_next_bus = min(METER_MAX_VALUE, predictions[prediction_index][1])
                    self.set_meter(multiplier * minutes_until_next_bus)                        

                    # sleep, but allow breaks
                    maintain_mode = self.sleep_until_input(5)
                    if not maintain_mode:
                        break  

            if not newly_in_mode:
                continue

            while self.current_mode == self.MODES.index('GOODREADS'):   
                
                if self.DEBUG:
                    print str(datetime.datetime.now()), 'goodreads mode'

                if newly_in_mode:
                    # last_update = 0
                    ben_stats = {}
                    kay_stats = {}

                    self.set_meter(0)
                    self.set_color()
                    self.update_leds()

                    maintain_mode = self.sleep_until_input(1)
                    if not maintain_mode:
                        break

                    self.start_blinking()

                # refresh if necessary
                # if (time.time() - last_update) > GOODREADS_REFRESH_TIMEOUT:
                ben_stats = gr.fetch_stats(GOODREADS_BEN_URL)
                kay_stats = gr.fetch_stats(GOODREADS_KAY_URL)
                    # last_update = time.time()

                if newly_in_mode:
                    self.stop_blinking()
                    newly_in_mode = False

                # calculate page differences
                current_year = str(datetime.datetime.now().year)
                ben_pages = ben_stats.get('year_stats', {}).get(current_year, 0)
                kay_pages = kay_stats.get('year_stats', {}).get(current_year, 0)
                kay_lead = round((kay_pages - ben_pages) / 100)                

                # set LEDs
                with lock:
                    # there's no time!
                    if kay_lead < 0:
                        self.set_color([0, 63, 63])                            
                    # you should maybe get going
                    elif kay_lead < 0:
                        self.set_color([0, 63, 0])
                    # plenty of time!
                    else:
                        self.set_color([63, 63, 63])
                    self.set_leds_to_mode()
                    self.update_leds()

                # set meter
                self.set_meter(max(-1 * METER_MAX_VALUE, min(kay_lead, METER_MAX_VALUE)))

                # sleep, but allow breaks
                maintain_mode = self.sleep_until_input(300)
                if not maintain_mode:
                    break                 


if __name__ == '__main__':
    
    b = BenKayMeter()
    b.main()

    # f = open('/var/log/benkaymeter-crash.log', 'a')
    # f.write(str(e))
    # f.close()

    # os.system('echo "%s" | mail -s "BEN/KAY METER CRASH LOG" thomas.j.lee@gmail.com' % str(e))

