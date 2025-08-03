from seleniumwire import UndetectedFirefox as UFF
from aiohttp.test_utils import TestServer
from loguru import logger
from mia.archiver.migrations import migrations
from mia.archiver.database import ArchiveDB
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


def test_server_runs_upgrade(server: TestServer, database: ArchiveDB):
    with database.connect() as conn:
        with conn.cursor() as cursor:
            assert database._get_migration_version(cursor) \
                == len(migrations)
