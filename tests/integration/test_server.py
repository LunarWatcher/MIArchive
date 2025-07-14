from seleniumwire import UndetectedFirefox as UFF
import pytest
from time import sleep
from aiohttp.test_utils import TestServer
from loguru import logger

def test_front_page(server: TestServer, driver: UFF):
    del driver.requests
    driver.get(
        str(server.make_url("/"))
    )

    assert driver.requests[0].response is not None
    assert driver.requests[0].response.status_code == 200
    logger.debug("Done")
