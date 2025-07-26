import os
from aiohttp import web
import aiohttp_jinja2 as ajp
import aiohttp_cors as aiocors
import jinja2
from loguru import logger
import msgspec
from xvfbwrapper import Xvfb

from mia import config
from mia.archiver.runner import Runner

from .middlewares import security_headers
from .app_keys import CONFIG, DATABASE, DEBUG, ARCHIVE_QUEUE
# Only used for types
import argparse

from .archive import ArchiveController
from .static import StaticController
from .api import ArchiveAPIController
from mia.www.locator import find as find_resource_dir

class ServerConfig(argparse.Namespace):
    debug: bool | None = False
    headed: bool = False

routes = web.RouteTableDef()

@routes.get('/')
@ajp.template("index.html")
async def index(request: web.Request):
    return {
        "Meta": {
            "Title": "MIArchive",
            "Description": "A small, self-hostable internet archive",
            # TODO: move  to a common function
            "Debug": request.app[DEBUG],
        }
    }

@routes.post("/api/debug/csp-reports")
async def report_csp_errors(request: web.Request):
    logger.debug("{}".format(await request.text()))
    return web.Response()

def load_config() -> config.Config:
    config_location = os.environ.get(
        "MIA_CONFIG_LOCATION",
        default="./config.json"
    )
    logger.debug("Attempting to load config from {}", config_location)
    if not os.path.exists(config_location):
        raise RuntimeError("Config not created")

    with open(config_location, "r") as f:
        return msgspec.json.decode(
            f.read(),
            type=config.Config
        )

async def cleanup(app):
    app[ARCHIVE_QUEUE].stop()

def inject_globals(app):
    app[CONFIG] = load_config()
    app[ARCHIVE_QUEUE] = Runner(app[CONFIG])

def start(args: ServerConfig, blocking: bool = True):
    if args.debug:
        logger.level("DEBUG")
        logger.warning("You're running MIA in debug mode.")

    app = web.Application(
        middlewares=[
            security_headers
        ],
    )
    inject_globals(app)
    app[DEBUG] = args.debug

    app.add_routes(routes)
    ajp.setup(
        app,
        loader=jinja2.FileSystemLoader(find_resource_dir())
    )

    cors = aiocors.setup(app)

    archive = ArchiveController(app)
    archive_api = ArchiveAPIController(app)
    static = StaticController(app)
    app.on_shutdown.append(cleanup)

    if blocking:
        # The display is initialised here to minimise problems with tests.
        # xvfbwrapper changes environment variables to Just Work:tm: with
        # things, but that means having two running in two threads (i.e. one in
        # a test and one in Runner) would cause all kinds of not fun problems
        with Xvfb() as display:
            web.run_app(
                app,
                port=app[CONFIG].server.port
            )
    else:
        return app

