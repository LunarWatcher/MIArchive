"""
The tests in this file run a full archival process on a test httpbin instance.
These tests are incredibly heavy, as they require setting up the full webdriver
used for the archival process, which at the time of writing has not been
optimised sufficiently.

These tests should be kept as minimal as possible, as these tests can be
responsible for 20-30 seconds of runtime _each_
"""
from threading import Condition
import msgspec
from aiohttp.test_utils import TestServer
import requests
import json
import os
import re

from mia.archiver.database import ArchiveDB
from mia.web.api.archive_api import ArchiveURLResponse
from mia.web.app_keys import ARCHIVE_QUEUE, CONFIG

def test_archival_storage(httpbin, database: ArchiveDB, server: TestServer):
    cv = Condition()
    def listener(event: dict):
        assert event["type"] == "empty"
        with cv:
            cv.notify_all()

    # TODO: this will be behind auth eventually, and the test needs to be
    # updated when that happens. Probably many of the tests will, so it might
    # make sense to add another mocking fixture specifically for API tokens
    queue = server.app[ARCHIVE_QUEUE]
    queue._callback(listener)
    res = requests.post(
        str(server.make_url("/api/archive/new")),
        data=json.dumps({
            "url": f"{httpbin.url}/html"
        })
    )
    assert res.status_code == 200
    decoded = msgspec.json.decode(
        res.text,
        type=ArchiveURLResponse
    )
    assert decoded.queue_size == 1
    # We have ~20 seconds + page load to get here, so there is no race
    # condition here
    # A timeout is necessary to address server-sided errors
    with cv:
        assert cv.wait(timeout=30)

    # The cv is synced back up when the queue becomes empty, so we now know
    # that the snpashot dir should exist, and the database should be populated
    config = server.app[CONFIG]
    assert os.path.exists(
        config.archive.snapshot_dir
    )
    dirs = [
        f.path
        for f in os.scandir(os.path.join(
            config.archive.snapshot_dir,
            "web"
        ))
        if f.is_dir()
    ]
    assert len(dirs) == 1
    # TODO: this test will fail in ~75 years
    assert re.match(
        r"^./__test_snapshots/web/20\d{18}$",
        dirs[0]
    )

    l = 0
    for path in os.scandir(dirs[0]):
        l += 1
        assert (
            "index.json" in path.path
            or (
                "http:__127.0.0.1:" in path.path
                and path.path.endswith("_html")
            )
        )

    assert l == 2

    with database.connect() as conn:
        with conn.cursor() as cursor:
            results = cursor.execute(
                """
                SELECT Url, RedirectURL, MimeType, HttpCode
                FROM mia.ArchiveEntries
                """
            ).fetchall()

            # The favicon 404s and is excluded by the filter system. I'm pretty
            # sure I'll be changing this at some point
            assert len(results) == 1
            row = results[0]
            assert re.match(
                r"http://127.0.0.1:\d+/html",
                row[0]
            )
            # /html is not a redirect
            assert row[1] is None
            # /html is (shock) HTML
            assert row[2] == "text/html"
            assert row[3] == 200
