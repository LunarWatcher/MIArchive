from aiohttp import web
from functools import partial
import os.path
from mia.www.locator import find as find_resource_dir

class StaticController:
    def __init__(self, app: web.Application):
        app.add_routes([
            web.get(
                "/static/style.css",
                partial(
                    self.load_file,
                    os.path.join(
                        find_resource_dir(),
                        "/static/style.css"
                    )
                )
            )
        ])

    def load_file(self, path, request):
        return web.FileResponse(
            path,
        )

