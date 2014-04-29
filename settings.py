PROJECT_HOME = '/home/pi/Devel/benkay'

NEXTBUS_URLS = {
	'42': 'http://www.nextbus.com/predictor/fancyBookmarkablePredictionLayer.shtml?a=wmata&stopId=1002070&r=42&d=42_42_0&s=7611',
	'43': 'http://www.nextbus.com/predictor/fancyBookmarkablePredictionLayer.shtml?a=wmata&r=43&d=43_43_0&s=7611'
}

SERIAL_DEVICE = '/dev/ttyAMA0'
SERIAL_SPEED = 115200

ROTARYENCODERPIN_A = 0
ROTARYENCODERPIN_B = 7
BLANKPIN = 2
GSCLKPIN = 3
METERPIN_A = 4
METERPIN_B = 5

CALIBRATION_FILE = '%s/calibration.json' % PROJECT_HOME

TIMEOUT = 300 # 5 minutes

NEXTBUS_ROUTES = [42, 43]

GOODREADS_LOGIN_URL = 'https://www.goodreads.com/user/sign_in'
GOODREADS_KAY_URL = 'https://www.goodreads.com/review/stats/62698-kay#pages'
GOODREADS_BEN_URL = 'https://www.goodreads.com/review/stats/980285-ben#pages'
GOODREADS_TOM_URL = 'https://www.goodreads.com/review/stats/4989865-tom-lee#pages'

def RUNKEEPER_TOKEN_DIRECTORY():
	return '%s/runkeeper_tokens' % PROJECT_HOME

try:
	from local_settings import *
except:
	pass