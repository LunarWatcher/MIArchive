import msgspec
import mia.archiver.storage as storage
from aiohttp import web
from loguru import logger
from mia.archiver.runner import Runner, ArchiveRequest
from .common import MessageResponse

from mia.config import Config
from mia.web.app_keys import CONFIG, ARCHIVE_QUEUE

class ArchiveURLRequest(msgspec.Struct):
    url: str
    depth: int | None = 1

class ArchiveURLResponse(msgspec.Struct):
    """
    Parameters:
        queue_size (int): Approximate position in the queue for the queued URL
                          Due to limitations of Python, this may be inaccurate,
                          and due to multithreading, it may be off by a few
    """
    queue_size: int

class ArchiveAPIController:
    def __init__(self, app: web.Application):
        app.add_routes([
            web.post(
                "/api/archive/new",
                self.post_archive
            )
        ])

    def post_archive(self, request: web.Request):
        config: Config = app[Config]
        storage.Storage(
            config.archive.snapshot_dir,
            type="web"
        )

        body = msgspec.json.decode(
            request.text,
            type=ArchiveURLRequest
        )

        queue: Runner = request.app[ARCHIVE_QUEUE]
        pos = queue.archive(ArchiveRequest(
            body.url,
            body.depth,
        ))

        return web.Response(
            body=msgspec.json.encode(MessageResponse(
                "OK",
                pos
            ))
        )
