import os
from aiohttp import web
import aiohttp_jinja2 as ajp
import aiohttp_cors as aiocors
import jinja2
from loguru import logger
import msgspec
from mia import config

from .middlewares import security_headers
from .archive import ArchiveController
from .app_keys import *
import argparse

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

def inject_globals(app):
    app[CONFIG] = load_config()

def start(args: ServerConfig, blocking: bool = True):
    if args.debug:
        logger.level("DEBUG")
        logger.warning("You're running MIA in debug mode.")

    app = web.Application(
        middlewares=[
            security_headers
        ],
    )
    app.add_routes(routes)
    ajp.setup(
        app,
        loader=jinja2.FileSystemLoader('./www')
    )

    cors = aiocors.setup(app)

    inject_globals(app)
    archive = ArchiveController(app)

    if blocking:
        web.run_app(
            app,
            port=app[CONFIG].server.port
        )
    else:
        return app

