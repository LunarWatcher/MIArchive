from functools import lru_cache
import msgspec
import mia.archiver.storage as storage
from mia.archiver.storage import ArchivedWebsite
from aiohttp import web
from .app_keys import SNAPSHOT_DIR
from loguru import logger

import os.path

@lru_cache
def load_page(index_path: str) -> ArchivedWebsite:
    with open(index_path, "rb") as f:
        return msgspec.json.decode(
            f.read(),
            type = storage.ArchivedWebsite
        )


class ArchiveController:
    def __init__(self, app: web.Application):
        app.add_routes([
            web.get(
                "/web/{timestamp}/{url:.*}",
                self.get_archived_page
            ),
            web.get(
                "/noscript/web/{timestamp}/{url:.*}",
                self.get_extra_sandboxed_archived_page
            )
        ])

    async def get_archived_page(self, request: web.Request):
        timestamp = request.match_info["timestamp"]
        url: str = request.match_info["url"]
        raw_url: str = url

        q = request.query_string
        if q is not None and q != "":
            q = "?" + q
            url += q


        index_file = os.path.join(
            request.app[SNAPSHOT_DIR],
            "web",
            timestamp,
            "index.json"
        )
        logger.debug("Requested {}", index_file)

        if not os.path.exists(index_file):
            return web.Response(
                text = "Timestamp not found"
            )

        json: ArchivedWebsite = load_page(index_file)
        if url not in json.pages:
            # TODO: find closest archived version instead maybe?
            # Would be useful for allowing links to be followed
            return web.Response(
                text = "Entry not found",
                status=404
            )

        # TODO: make example.com and example.com/ the same url:tm:
        # (using urlparse might be an option, I think the / is introduced
        # somewhere there)
        metadata = json.pages[url]

        if (metadata.status_code >= 300 and metadata.status_code < 400):
            return web.Response(
                text = "IOU 1x redirect feature"
            )

        with open(metadata.filepath, "rb") as f:
            return web.Response(
                body = f.read(),
                content_type = metadata.mime_type,
                status = metadata.status_code,
                charset="utf-8"
            )

    async def get_extra_sandboxed_archived_page(self, request):
        return await self.get_archived_page(request)

