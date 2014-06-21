import time

PROJECT_HOME = '/home/pi/Devel/benkaymeter'

NEXTBUS_URLS = {
	'G2': 'http://www.nextbus.com/api/pub/v1/agencies/wmata/routes/G2/stops/13134/predictions?coincident=true&direction=G2_G2_0'
}

NEXTBUS_ROUTES = ['G2']

GOODREADS_LOGIN_URL = 'https://www.goodreads.com/user/sign_in'
GOODREADS_KAY_URL = 'https://www.goodreads.com/review/stats/62698-kay#pages'
GOODREADS_BEN_URL = 'https://www.goodreads.com/review/stats/980285-ben#pages'
GOODREADS_TOM_URL = 'https://www.goodreads.com/review/stats/4989865-tom-lee#pages'
GOODREADS_REFRESH_TIMEOUT = 300

BIKESHARE_XML_URL = 'http://www.capitalbikeshare.com/data/stations/bikeStations.xml'
BIKESHARE_STATION_IDS = [31636, 31509]
BIKESHARE_REFRESH_RATE = 120

def RUNKEEPER_TOKEN_DIRECTORY():
	return '%s/runkeeper_tokens' % PROJECT_HOME
RUNKEEPER_REFRESH_RATE = 600

ROTARYENCODERPIN_A = 0
ROTARYENCODERPIN_B = 7
BLANKPIN = 2
GSCLKPIN = 3
METERPIN_A = 4
METERPIN_B = 5

METER_MAX_VALUE = 25


CALIBRATION_FILE_A = '%s/calibration_4.json' % PROJECT_HOME
CALIBRATION_FILE_B = '%s/calibration_5.json' % PROJECT_HOME

TIMEOUT = 300 # 5 minutes

try:
	from local_settings import *
except:
	pass
