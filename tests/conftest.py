import pytest
import os
import mia.web.server
from seleniumwire import UndetectedFirefox
from .utils import create_config
from xvfbwrapper import Xvfb
from aiohttp import web
import asyncio
from aiohttp.test_utils import TestServer
from loguru import logger
from threading import Thread

from time import sleep
import asyncio
import requests

@pytest.fixture(scope="session", autouse=True)
def init_display():
    xvfb = Xvfb()
    xvfb.start()
    yield xvfb
    xvfb.stop()

@pytest.fixture(scope="function")
def server():
    os.environ["MIA_CONFIG_LOCATION"] = "./__test_config.json"
    if not os.path.exists(os.environ["MIA_CONFIG_LOCATION"]):
        create_config(os.environ["MIA_CONFIG_LOCATION"])

    inst = mia.web.server.start(mia.web.server.ServerConfig(
        debug=False,
        headed=False
    ), blocking=False)

    loop = asyncio.new_event_loop()
    serv = TestServer(
        inst,
        loop=loop
    )

    def start_loop(loop: asyncio.BaseEventLoop):
        # This sleep is inexplicably required for the tests to not occasionally
        # freeze for no reason whatsoever
        sleep(1.0)
        asyncio.set_event_loop(loop)
        try:
            loop.run_forever()
        finally:
            loop.close()

    t = Thread(
        target=start_loop,
        args=(loop,),
        daemon=True
    )
    t.start()
    loop.create_task(serv.start_server())
    while not serv.started:
        sleep(0.3)
    logger.debug("Server started on port {}", serv.port)
    yield serv
    loop.create_task(serv.close())
    # Inexplicably  required for Runner to shut down correctly
    # I would assume these aren't called because we're bypassing the entire
    # shutdown mechanism, so the async methods stored here aren't called.
    # Unfortunately. server.py::cleanup() is loadbearing, so they need ot be
    # called manually
    for func in inst.on_shutdown:
        loop.create_task(func(inst))
    loop.stop()
    # This request is inexplicably required for the loop to terminate. It dies
    # as soon as the request is received, but some kind of event has to trigger
    # the actual shutdown after `.stop()`. Waiting does nothing here
    try:
        requests.get(str(serv.make_url("/")))
    except:
        # It also causes a connection reset exception to be thrown that we have
        # to ignore, because idfk, fuck you I guess
        pass
    t.join()
    os.remove(os.environ["MIA_CONFIG_LOCATION"])

@pytest.fixture(scope="function")
def mock_site():
    pass

@pytest.fixture(scope="function")
def driver():
    browser = UndetectedFirefox()
    browser.set_page_load_timeout(2)
    yield browser
    browser.quit()
