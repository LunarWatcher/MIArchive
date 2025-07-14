from seleniumwire import UndetectedFirefox as UFF
import pytest
from time import sleep
from aiohttp.test_utils import TestServer
from loguru import logger
from tests.utils import find_first

def test_front_page(server: TestServer, driver: UFF):
    del driver.requests
    driver.get(
        str(server.make_url("/"))
    )

    page_request = find_first(driver, "localhost", server.port)

    assert page_request.response is not None
    assert page_request.response.status_code == 200
    logger.debug("Done")
