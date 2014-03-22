from settings import *
import scrapelib
import time
import re
from BeautifulSoup import BeautifulSoup
from soupselect import select

class NextbusPredictor(object):
	"""Tracks Nextbus arrival times"""
	def __init__(self, routes):
		super(NextbusPredictor, self).__init__()
		self.routes = map(lambda x: str(x), routes)
		self.predictions = {}
		self.last_refresh = {}
		self.scraper = scrapelib.Scraper(requests_per_minute=10, follow_robots=False)
		for r in self.routes:
			self.predictions[r] = None
			self.last_refresh[r] = None
			self.refresh(r)
	
	def _clean_prediction_html(self, html):
		return re.sub(r'&nbsp;','', re.sub(r'<[^>]*>','',(str(html)), flags=re.MULTILINE|re.DOTALL)).strip()

	def _extract_predictions(self, html):
		if '<p class="predictHead"><nobr><span id=\'i18n_en\'>No current prediction' in html:
			return None
		else:
			predictions = []
			soup = BeautifulSoup(html)	

			# get the primary/imminent prediction		
			try:
				minutes = self._clean_prediction_html(select(soup, '.predictionNumberForFirstPred')[0])
			except:
				return None
			if ('departing' in minutes.lower()) or ('arriving' in minutes.lower()):
				predictions.append(0)
			else:
				predictions.append(int(minutes))

			# get the other predictions
			for m in select(soup, '.predictionNumberForOtherPreds'):
				m = self._clean_prediction_html(m)
				try:
					predictions.append(int(m))
				except:
					pass

			return predictions

	def refresh(self, route):
		"""Force a refresh of a specific route"""
		route = str(route)

		url = NEXTBUS_URLS.get(str(route), False)
		if not url:
			return

		try:
			html = self.scraper.urlopen(url)
		except:
			return # fail silently. bad, I know.

		self.predictions[route] = self._extract_predictions(html)
		self.last_refresh[route] = time.time()

	def _get_query_frequency(self, last_prediction_in_minutes):
		if last_prediction_in_minutes>20:
			return (last_prediction_in_minutes / 2) * 60
		elif last_prediction_in_minutes>10:
			return 3 * 60
		elif last_prediction_in_minutes>5:
			return 2 * 60
		else:
			return 60

	def refresh_if_necessary(self):
		"""Only refresh prediction times intermittently -- don't hammer"""
		for r in self.routes:
			if self.predictions[r] is None:
				if (time.time() - self.last_refresh[r]) > TIMEOUT:
					self.refresh(r)
			else:
				# if we have a prediction, refresh if we're halfway or more to
				# the expected arrival time
				if (time.time() - self.last_refresh[r]) > self._get_query_frequency(self.predictions[r][0]):
					self.refresh(r)
	
	def _adjust_prediction_for_elapsed_time(self, prediction, r):
		return round(prediction - round((time.time() - self.last_refresh[r]) / 60.0))

	def get_closest_arrival(self):
		return self.get_nth_closest_arrival(0)

	def get_nth_closest_arrival(self, n=0, route=None):
		"""Return the (route, arrival) pair that's happening soonest"""
		arrivals = []
		for r in self.routes:			
			if self.predictions.get(r) is not None:			
				for p in self.predictions.get(r, []):
					valid_route = route is None
					valid_route = valid_route or ((type(route) in (tuple, list)) and (r in route))
					valid_route = valid_route or route==r
					if valid_route:
						arrivals.append( (p, r) )

		if n>=len(arrivals):
			return None

		matching_arrival = sorted(arrivals, key=lambda x: x[0])[n]
		return (matching_arrival[1], self._adjust_prediction_for_elapsed_time(matching_arrival[0], matching_arrival[1]))


if __name__ == '__main__':
	main()
