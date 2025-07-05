import os
from aiohttp import web
import aiohttp_jinja2 as ajp
import jinja2
import filetype

from .middlewares import security_headers

routes = web.RouteTableDef()

# TODO: make configurable
SNAPSHOT_DIR = "./snapshots/"

def get_content_type(url: str):
    ext = url.rsplit(".", maxsplit=1)[-1]
    print(ext)
    if ext == "js" or ext == "mjs":
        return "text/javascript"
    elif ext == "css":
        return "text/css"
    elif ext == "svg":
        return "image/svg+xml"

    return "text/html"

@routes.get('/')
async def hello(request):
    return web.Response(text="Hello, world")

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
        return web.Response(text="Not found", status = 404)

    # TODO: I probably want to store the mimetypes returned when yoinking
    # the pages so I don't need to do this shit 
    ft = filetype.guess(expected_url)
    if ft == None:
        with open(expected_url, "r") as f:
            print(expected_url)
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


def start(args):
    app = web.Application(middlewares = [
        security_headers
    ])
    app.add_routes(routes)
    ajp.setup(app,
        loader=jinja2.FileSystemLoader('./www'))
    web.run_app(app)

