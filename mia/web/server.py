import os
from aiohttp import web
import aiohttp_jinja2 as ajp
import aiohttp_cors as aiocors
import jinja2
import filetype
from loguru import logger

from .middlewares import security_headers

routes = web.RouteTableDef()

# TODO: make configurable
SNAPSHOT_DIR = "./snapshots/"

def get_content_type(url: str):
    ext = url.rsplit(".", maxsplit=1)[-1]
    if ext == "js" or ext == "mjs":
        return "text/javascript"
    elif ext == "css":
        return "text/css"
    elif ext == "svg":
        return "image/svg+xml"

    return "text/html"

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

@routes.get("/web/{timestamp}/{url:.*}")
async def get_archived_page(request):
    timestamp = request.match_info["timestamp"]
    url: str = request.match_info["url"]
    raw_url: str = url

    q = request.query_string
    if q is not None and q != "":
        q = "?" + q
        url += q

    expected_url = os.path.join(
        SNAPSHOT_DIR,
        "web",
        timestamp,
        url.replace("/", "_")
    )

    if not os.path.exists(expected_url):
        logger.debug("Tried to request {}", expected_url)
        return web.Response(
            text="\"Not found\"", status = 404,
            content_type="text/plain",
        )

    # TODO: I probably want to store the mimetypes returned when yoinking
    # the pages so I don't need to do this shit 
    ft = filetype.guess(expected_url)
    if ft == None:
        with open(expected_url, "r") as f:
            res = web.Response(
                text = f.read(),
                content_type=get_content_type(raw_url)
            )
            return res
    else:
        with open(expected_url, "rb") as f:
            res = web.Response(
                body = f.read()
            )
            return res

@routes.get("/noscript/web/{timestamp}/{url:.*}")
async def get_extra_sandboxed_archived_page(request):
    return await get_archived_page(request)


def start(args):
    if args.debug:
        logger.level("DEBUG")
        logger.warning("You're running MIA in debug mode.")

    app = web.Application(middlewares = [
        security_headers
    ])
    app.add_routes(routes)
    ajp.setup(app,
        loader=jinja2.FileSystemLoader('./www'))

    cors = aiocors.setup(app)

    web.run_app(app)

