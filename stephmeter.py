#!/home/pi/.virtualenvs/stephmeter/bin/python

import nextbus
import pwm_calibrate
import led
import time
import datetime
import sys
from settings import *

def main():
	DEBUG = '--debug' in map(lambda x: x.lower().strip(), sys.args)

	if DEBUG:
		print 'Entering debug mode...'
	else:
		l = led.LED(SERIAL_DEVICE, SERIAL_SPEED)
		p = pwm_calibrate.PWMCalibrator(smoothing=True)
		p.load()
		p_range = p.get_range()

	nb = nextbus.NextbusPredictor(NEXTBUS_ROUTES)

	while True:
		nb.refresh_if_necessary()

		# determine the number of predictions to display based on time of day and interval between
		num_predictions_to_display = 1
		predictions = (nb.get_nth_closest_arrival(0), nb.get_nth_closest_arrival(1))
		if not (None in predictions):
			if (predictions[0][1] is not None) and (predictions[1][1] is not None): # do we have two valid predictions?
				if predictions[0][1]<30: # is the next bus less than 30m away?
					if predictions[1][1]<p_range[1]: # does the second one fit on the meter?
						num_predictions_to_display = 2


		for (route, minutes) in predictions[:num_predictions_to_display]:
			
			if minutes is None:
				minutes = p_range[1]

			minutes = min(max(minutes, p_range[0]), p_range[1])

			if DEBUG:
				print 'route is %s, arriving in %d minutes' % (route, minutes)
			else:
				if int(route)==43:
					l.set(50, 100, 50)
				elif int(route)==42:
					l.set(50, 50, 100)
				p.setPWM(minutes)

			time.sleep(3)


if __name__ == '__main__':
	main()

