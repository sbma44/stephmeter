import time

PROJECT_HOME = '/home/pi/Devel/benkaymeter'

def g2_url():
	return 'http://www.nextbus.com/api/pub/v1/agencies/wmata/routes/G2/stops/13134/predictions?coincident=true&direction=G2_G2_0&key=61d4507fad79cee8a18aea5174a4acdf&timestamp=%d' % (int(time.time())/1000)

NEXTBUS_URLS = {
	'G2': g2_url
}

NEXTBUS_ROUTES = ['G2']

GOODREADS_LOGIN_URL = 'https://www.goodreads.com/user/sign_in'
GOODREADS_KAY_URL = 'https://www.goodreads.com/review/stats/62698-kay#pages'
GOODREADS_BEN_URL = 'https://www.goodreads.com/review/stats/980285-ben#pages'
GOODREADS_TOM_URL = 'https://www.goodreads.com/review/stats/4989865-tom-lee#pages'

BIKESHARE_XML_URL = 'http://www.capitalbikeshare.com/data/stations/bikeStations.xml'
BIKESHARE_STATION_IDS = [31636, 31509]



ROTARYENCODERPIN_A = 0
ROTARYENCODERPIN_B = 7
BLANKPIN = 2
GSCLKPIN = 3
METERPIN_A = 4
METERPIN_B = 5

CALIBRATION_FILE_A = '%s/calibration_4.json' % PROJECT_HOME
CALIBRATION_FILE_B = '%s/calibration_5.json' % PROJECT_HOME

TIMEOUT = 300 # 5 minutes

def RUNKEEPER_TOKEN_DIRECTORY():
	return '%s/runkeeper_tokens' % PROJECT_HOME

try:
	from local_settings import *
except:
	pass
