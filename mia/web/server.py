from contextlib import nullcontext
import os
import sys
from aiohttp import web
import aiohttp_jinja2 as ajp
import aiohttp_cors as aiocors
import jinja2
from loguru import logger
import msgspec
from xvfbwrapper import Xvfb

from mia import config
from mia.archiver.database import ArchiveDB, DBConf
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
    app[ARCHIVE_QUEUE] = Runner(app[CONFIG])

def start(args: ServerConfig, blocking: bool = True):
    if args.debug:
        # TODO: configuring logging levels in loguru is absolute cancer. Might
        # want to switch to another library that handles it better
        # TODO: Until then, this needs to be set at every single entry point
        # for the application where there is a reason to set it. At the time of
        # writing, only the server has a `--debug` flag.
        logger.configure(handlers=[{
            "sink": sys.stdout,
            "level": "DEBUG"
        }])
        logger.warning("You're running MIA in debug mode.")
    else:
        logger.configure(handlers=[{
            "sink": sys.stdout,
            "level": "INFO"
        }])

    app = web.Application(
        middlewares=[
            security_headers
        ],
    )
    app[DEBUG] = args.debug or False
    conf = load_config()
    app[CONFIG] = conf
    app[DATABASE] = ArchiveDB(
        conf.database.database,
        conf.database.host,
        conf.database.username,
        conf.database.password,
        DBConf(
            upgrade=True
        )
    )
    # TODO: why do I keep this?
    inject_globals(app)

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
        logger.debug("Display: {}", args.headed)
        # The display is initialised here to minimise problems with tests.
        # xvfbwrapper changes environment variables to Just Work:tm: with
        # things, but that means having two running in two threads (i.e. one in
        # a test and one in Runner) would cause all kinds of not fun problems
        with (Xvfb() if not args.headed else nullcontext()) as display:
            web.run_app(
                app,
                port=app[CONFIG].server.port
            )
    else:
        return app

