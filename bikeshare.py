import xml.etree.ElementTree as ET
import requests

from settings import *

class BikeShareInterface(object):
	"""Fetch bikeshare availability"""
	def __init__(self):
		super(BikeShareInterface, self).__init__()
		self.last_updated = None
		self.bike_availability = dict.fromkeys(BIKESHARE_STATION_IDS)
		for x in self.bike_availability:
			self.bike_availability[x] = {}
		
	def refresh(self):
		r = requests.get(BIKESHARE_XML_URL)
		root = ET.fromstring(r.content)
		
		self.last_updated = root.get('lastUpdate')
		for station in root.iter('station'):
			station_id = int(station.find('terminalName').text)
			if station_id in BIKESHARE_STATION_IDS:
				self.bike_availability[station_id]['bikes'] = int(station.find('nbBikes').text)
				self.bike_availability[station_id]['docks'] = int(station.find('nbEmptyDocks').text)

if __name__ == '__main__':
	bs = BikeShareInterface()
	bs.refresh()
	print bs.bike_availability