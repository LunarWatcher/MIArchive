import os
from os.path import exists
from aiohttp import web
import aiohttp_jinja2 as ajp
import aiohttp_cors as aiocors
import jinja2
import filetype
from loguru import logger
import msgspec

from mia.archiver import storage

from .middlewares import security_headers
from .archive import ArchiveController
from .app_keys import *

routes = web.RouteTableDef()

@routes.get('/')
@ajp.template("index.html")
async def index(request: web.Request):
    return {
        "Meta": {
            "Title": "MIArchive",
            "Description": "A small, self-hostable internet archive",
        }
    }

@routes.post("/api/debug/csp-reports")
async def report_csp_errors(request: web.Request):
    logger.debug("{}".format(await request.text()))
    return web.Response()


def inject_globals(app):
    app[SNAPSHOT_DIR] = "./snapshots/"

def start(args):
    if args.debug:
        logger.level("DEBUG")
        logger.warning("You're running MIA in debug mode.")

    app = web.Application(middlewares = [
        security_headers
    ])
    app.add_routes(routes)
    ajp.setup(
        app,
        loader=jinja2.FileSystemLoader('./www')
    )

    cors = aiocors.setup(app)

    inject_globals(app)
    archive = ArchiveController(app)

    web.run_app(app)

