from aiohttp.web import AppKey
from mia import config

DEBUG = AppKey("debug", bool)
DATABASE = AppKey("database", None)
CONFIG = AppKey("config", config.Config)
