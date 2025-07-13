from aiohttp.web import AppKey
from mia import config

DATABASE = AppKey("database", None)
CONFIG = AppKey("config", config.Config)
