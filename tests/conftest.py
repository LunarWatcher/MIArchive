import msgspec
import pytest
import os
import shutil
from mia.archiver.database import ArchiveDB
from mia.archiver.dbo.user import UserDBO
from mia.archiver.migrations import Migrator
import mia.archiver.database
import mia.config
import mia.web.server

from seleniumwire import UndetectedFirefox

from tests.support.fixture_objects import MockUsers
from .utils import create_config
from xvfbwrapper import Xvfb
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

@pytest.fixture(scope="session")
def config():
    os.environ["MIA_CONFIG_LOCATION"] = "./__test_config.json"
    if not os.path.exists(os.environ["MIA_CONFIG_LOCATION"]):
        create_config(os.environ["MIA_CONFIG_LOCATION"])

    with open(os.environ["MIA_CONFIG_LOCATION"], "r") as f:
        conf = msgspec.json.decode(
            f.read(),
            type=mia.config.Config
        )
    assert isinstance(conf, mia.config.Config)
    yield conf

    os.remove(os.environ["MIA_CONFIG_LOCATION"])
    if os.path.exists(conf.archive.snapshot_dir):
        shutil.rmtree(conf.archive.snapshot_dir)

@pytest.fixture(scope="function")
def database(config: mia.config.Config):
    """
    Initialises a database that doesn't automatically run migrations. This
    should only be used for general database setup (the yielded db instance is
    untouched), or for accessing data after the database has been initialised
    """
    db = ArchiveDB(
        config.database.database,
        config.database.host,
        config.database.username,
        config.database.password,
        mia.archiver.database.DBConf(
            upgrade=False,
            _allow_unupgraded=True
        )
    )
    yield db
    logger.debug("Killing database")

    with db.connect() as conn:
        with conn.cursor() as cursor:
            # This could use the migrator instead, but that risks leaving the
            # database in an inconsistent state, which fails later tests
            cursor.execute("DROP SCHEMA mia CASCADE;")

@pytest.fixture(scope="function")
def udatabase(database: ArchiveDB):
    """
    Shorthand for "Upgraded DATABASE". Same as `database`, but with migrations
    run as part of the fixture

    This should only be used for database tests that assume the latest
    migration is in effect
    """
    with database.connect() as conn:
        with conn.cursor() as cursor:
            migrator = Migrator(cursor)
            migrator.upgrade()

    yield database

@pytest.fixture(scope="function")
def server(database, config):
    inst = mia.web.server.start(mia.web.server.ServerConfig(
        debug=True,
        headed=False
    ), blocking=False)
    # Makes pyright stfu
    assert inst is not None

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

@pytest.fixture(scope="function")
def mock_users(udatabase: ArchiveDB):
    """
    Creates a standard set of users, and returns a list of user credentials.
    """
    users = MockUsers(
        UserDBO("user", "password69", False),
        UserDBO("user2", "password420", False),
        UserDBO("admin", "admin", True),
    )
    with udatabase.connect() as conn:
        with conn.cursor() as cursor:
            for user in users.iter():
                udatabase.create_user(
                    cursor,
                    user.username,
                    user.password,
                    user.admin
                )

    yield users

@pytest.fixture(scope="function")
def mock_snapshots(udatabase: ArchiveDB, config: mia.config.Config):
    # TODO: implement
    # This function needs to:
    # 1. hard link the directories (?) in mock_snapshots/ to __test_snapshots
    #   (use the config variable for the path)
    # 2. Trigger a reindex of the snapshot dir.
    #
    # At the time of writing, #2 is impossible, because no reindexing happens.
    # If this remains the case, step 2 is instead to add the entries to the
    # database manually.
    # The JSON file should contain pretty much everything that goes into the
    # database anyway, as the database is primarily supportive for the search
    # functionality that also doesn't exist yet at the time of writing
    pass

@pytest.fixture(scope="function")
def driver():
    browser = UndetectedFirefox()
    browser.set_page_load_timeout(2)
    yield browser
    browser.quit()
