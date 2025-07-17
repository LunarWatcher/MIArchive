from aiohttp import web
from functools import partial
import os.path
from mia.www.locator import find as find_resource_dir
from loguru import logger

class StaticController:
    def __init__(self, app: web.Application):
        CSS = "text/css"
        JS = "text/javascript"
        resource_dir = str(find_resource_dir())
        assert resource_dir is not None
        assert len(resource_dir) != 0
        app.add_routes([
            web.get(
                "/static/style.css",
                partial(
                    self.load_file,
                    os.path.join(
                        resource_dir,
                        "static/style.css"
                    ),
                    CSS
                )
            )
        ])

    async def load_file(self, path, mimetype, _):
        logger.debug("{}: {}", path, mimetype)
        return web.FileResponse(
            path,
            headers={
                "Content-Type": mimetype
            }
        )

