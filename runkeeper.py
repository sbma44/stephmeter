import os
import json
import time
import datetime

import requests

from settings import *

class RunKeeperInterface(object):
	def __init__(self):
		super(RunKeeperInterface, self).__init__()

		self.tokens = {}
		self.activity = {}

		for filename in os.listdir(RUNKEEPER_TOKEN_DIRECTORY()):
			f = open('%s/%s' % (RUNKEEPER_TOKEN_DIRECTORY(), filename), 'r')
			self.tokens[filename] = json.load(f)
			self.tokens[filename]['updated'] = None
			f.close()

	def _meters_to_miles(self, meters):
		return (meters / 1609.34)

	def _convert_date_string(self, date_string):
		return datetime.datetime.strptime(date_string, '%a, %d %b %Y %H:%M:%S')

	def refresh(self, token_name):
		access_token = self.tokens.get(token_name, {}).get('access_token', '')
		r = requests.get('http://api.runkeeper.com/fitnessActivities?pageSize=100', headers={'Authorization': 'Bearer %s' % access_token, 'Accept': 'application/vnd.com.runkeeper.FitnessActivityFeed+json'})
		self.activity[token_name] = json.loads(r.content)
		self.tokens[token_name]['updated'] = time.time()

	def refresh_all(self):
		for token_name in list(self.tokens):
			self.refresh(token_name)

	def calculate_mileage(self, token_name):
		mileage = 0
		# print self.tokens.get(token_name, {})
		for activity in self.activity.get(token_name, {}).get('items', []):			
			# ensure activity is running
			if activity.get('type').lower()=='running':
				# ensure activity is from present week
				activity_date = self._convert_date_string(activity.get('start_time', 'Wed, 1 Jan 2014 00:00:00'))				
				if int(datetime.datetime.now().strftime('%U'))==int(activity_date.strftime('%U')):
					mileage += self._meters_to_miles(float(activity.get('total_distance')))
		return mileage
		
if __name__ == '__main__':
	rki = RunKeeperInterface()
	rki.refresh_all()
	print rki.calculate_mileage('stephstepht')