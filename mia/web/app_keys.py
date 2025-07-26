from aiohttp.web import AppKey
from mia import config
from mia.archiver.runner import Runner

DEBUG = AppKey("debug", bool)
DATABASE = AppKey("database", None)
CONFIG = AppKey("config", config.Config)
ARCHIVE_QUEUE = AppKey("archive_queue", Runner)
