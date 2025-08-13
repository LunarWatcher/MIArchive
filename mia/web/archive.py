from functools import lru_cache
import msgspec
import mia.archiver.storage as storage
from mia.archiver.storage import ArchivedWebsite
from aiohttp import web
from .app_keys import CONFIG, DEBUG, ARCHIVE_QUEUE
from loguru import logger
import aiohttp_jinja2 as ajp
from mia.archiver.runner import Runner, ArchiveRequest

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
            ),
            web.get(
                "/search",
                self.get_search
            ),
            web.get(
                "/go",
                self.get_go,
            ),
            web.get(
                "/archive",
                self.get_archive
            )
        ])

    async def get_search(self, request: web.Request):
        pass

    async def get_go(self, request: web.Request):
        """
        Handles the form request from the front page
        """
        action = request.query["action"]
        url = request.query["url"]
        if action is None or action not in ["search", "archive"]:
            return web.Response(
                body="You appear to have manually edited the query. You did a dumb",
                status=400,
            )

        if url is None:
            return web.Response(
                body="Missing URL",
                status=400
            )

        if action == "search":
            return web.HTTPTemporaryRedirect(
                # TODO: is this actually safe?
                "/search?url=" + url
            )
        elif action == "archive":
            return web.HTTPTemporaryRedirect(
                # TODO: is this actually safe?
                "/archive?url=" + url
            )
        else:
            raise RuntimeError("You fucked up")

    async def get_archive(self, request: web.Request):
        # TODO: auth (middleware?)

        url = request.query["url"]
        if url is None:
            return web.Response(
                body="Missing URL to archive",
                code = 400
            )

        queue: Runner = request.app[ARCHIVE_QUEUE]
        pos = queue.archive(ArchiveRequest(
            url,
            # TODO: make configurable? This is currently only settable through
            # the API
            1,
        ))

        return ajp.render_template(
            "archive.html", request, {
                "Meta": {
                    "Title": "Archiving in progress",
                    "Description": "Progress page for the archiver",
                    "Debug": request.app[DEBUG]
                },
                "Position": pos
            }
        )

    async def get_archived_page(self, request: web.Request):
        timestamp = request.match_info["timestamp"]
        url: str = request.match_info["url"]
        raw_url: str = url

        q = request.query_string
        if q is not None and q != "":
            q = "?" + q
            url += q


        index_file = os.path.join(
            request.app[CONFIG].archive.snapshot_dir,
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
            # Before giving up, check if there's a trailing / variant archived,
            # or in the case of provided URLs with a trailing slash, if there's
            # a variant without it archived.
            if raw_url.endswith("/"):
                url = raw_url[:-1] + q
            else:
                url = raw_url + "/" + q

            if url not in json.pages:
                # TODO: find closest archived version instead maybe?
                # Would be useful for allowing links to be followed
                return web.Response(
                    text = "Entry not found",
                    status=404
                )
            else:
                return self._create_redirect(
                    request,
                    timestamp,
                    url
                )

        # TODO: make example.com and example.com/ the same url:tm:
        # (using urlparse might be an option, I think the / is introduced
        # somewhere there)
        metadata = json.pages[url]

        if (metadata.status_code >= 300 and metadata.status_code < 400):
            return self._create_redirect(
                request,
                timestamp,
                metadata.redirect_target,
                metadata.original_url
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

    def _resolve_relative_urls(self, path, base):
        # TODO: there must be a library that does this
        if path.startswith("//"):
            # TODO: can this even appear in redirects?
            return "https:" + path
        elif path.startswith("/"):
            if base.endswith("/"):
                base = base[:-1]
            return base + path
        return path

    def _create_redirect(
        self,
        request: web.Request,
        timestamp: str,
        target_url: str,
        base_url: str = None
    ):
        resolved_url = self._resolve_relative_urls(
            target_url,
            base_url
        )
        target_path = str(request.rel_url)

        target_path = target_path[1:].split("/", 1)
        builder = "/"
        if target_path[0] == "noscript":
            builder += "noscript/"
        builder += f"web/{timestamp}/{resolved_url}"

        return web.HTTPPermanentRedirect(
            builder
        )

