#!/home/pi/.virtualenvs/markmograph/bin/python

import nextbus2
import envoy
import time
import datetime
import hashlib
import sys
import os
from settings import *

DEBUG = '--debug' in map(lambda x: x.lower().strip(), sys.argv)

def play_sound(stop_id):
	if DEBUG:
		print 'playing sound for %s' % stop_id
	try:
		if STOPS_AND_THEIR_SOUND_FILES[stop_id]['type']=='mp3':
			envoy.run('/usr/bin/mpg321 %s' % (STOPS_AND_THEIR_SOUND_FILES[stop_id]['path']))
		if STOPS_AND_THEIR_SOUND_FILES[stop_id]['type']=='wav':
			envoy.run('/usr/bin/aplay %s' % (STOPS_AND_THEIR_SOUND_FILES[stop_id]['path']))
	except Exception, e:
		print 'attempted to play %s' % STOPS_AND_THEIR_SOUND_FILES[stop_id]['path']

def main():

	if DEBUG:
		print 'Entering debug mode...'

	check_times = {}

	# hash sound filenames, detect type, retrieve if necessary
	for (stop_id, sound_file) in STOPS_AND_THEIR_SOUND_FILES.items():
		STOPS_AND_THEIR_SOUND_FILES[stop_id] = {'sound_file': sound_file}
		STOPS_AND_THEIR_SOUND_FILES[stop_id]['hash'] = hashlib.sha256(sound_file).hexdigest()
		STOPS_AND_THEIR_SOUND_FILES[stop_id]['type'] = sound_file.split('.')[-1].lower().strip()
		STOPS_AND_THEIR_SOUND_FILES[stop_id]['path'] = "%s/sounds/%s.%s" % (WORKING_DIRECTORY, STOPS_AND_THEIR_SOUND_FILES[stop_id]['hash'], STOPS_AND_THEIR_SOUND_FILES[stop_id]['type'])
		if not os.path.exists(STOPS_AND_THEIR_SOUND_FILES[stop_id]['path']):
			if DEBUG:
				print 'retrieving %s' % (sound_file)
			envoy.run('curl "%s" -o "%s"' % (sound_file, STOPS_AND_THEIR_SOUND_FILES[stop_id]['path']))
		check_times[stop_id] = 0

	while True:
		for (stop_id, ct) in check_times.items():
			
			played_sound = False

			if time.time()>ct:
				if DEBUG:
					print 'checking times for stop %s' % stop_id

				predictions = None
				while predictions is None:
					try:
						predictions = nextbus2.get_predictions_for_stop(AGENCY_TAG, stop_id).predictions
					except:
						time.sleep(60)

				if len(predictions)==0:
					check_times[stop_id] = time.time() + (10*60)
				else:
					shortest_time = predictions[0].seconds
					for p in predictions:
						if p.seconds<PLAY_SOUND_IF_BUS_IS_LESS_THAN_THIS_MANY_SECONDS_AWAY:
							play_sound(stop_id)
							played_sound = True
						shortest_time = min(shortest_time, p.seconds)

					if shortest_time>180:
						check_times[stop_id] = time.time() + (shortest_time/2)
					else:
						if played_sound:
							check_times[stop_id] = time.time() + (PLAY_SOUND_IF_BUS_IS_LESS_THAN_THIS_MANY_SECONDS_AWAY * 2)
						else:
							check_times[stop_id] = time.time() + 30

					if DEBUG:
						print 'will check %s again in %d seconds' % (stop_id, (check_times[stop_id] - time.time()))

		time.sleep(1)


if __name__ == '__main__':

	try:
		main()
	except Exception, e:
		raise e
		f = open('/var/log/markmograph-crash.log', 'a')
		f.write(str(e))
		f.close()

		os.system('echo "%s" | mail -s "MARKMOGRAPH CRASH LOG" thomas.j.lee@gmail.com' % str(e))

