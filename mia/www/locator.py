import pathlib
from loguru import logger

def find():
    p = pathlib.Path(__file__).parent.resolve()
    logger.debug("Resource directory found at {}", p)
    return p
