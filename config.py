# Read configuration information from config.ini
import configparser
from datetime import timedelta

config = configparser.ConfigParser()
config.read('config.ini')

CONFIG_AUTH_SECTION = 'AUTHORIZATION'
SECRET_KEY = config.get(CONFIG_AUTH_SECTION, "SECRET_KEY")
ALGORITHM = config.get(CONFIG_AUTH_SECTION, "ALGORITHM") 
ACCESS_TOKEN_EXPIRE_MINUTES = int(config.get(CONFIG_AUTH_SECTION, "ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(config.get(CONFIG_AUTH_SECTION, "REFRESH_TOKEN_EXPIRE_MINUTES"))