
from collections.abc import Awaitable, Callable
from aiohttp import web


@web.middleware
async def security_headers(
    request: web.Request,
    handler: Callable[[web.Request], Awaitable[web.StreamResponse]]
) -> web.StreamResponse:
    res = await handler(request)
    res.headers.merge({
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "X-XSS-Protection": "0",
    })

    if (request.url.path.startswith("/web/") or
            request.url.path.startswith("/noscript/web/")):
        # The CSP on these pages needs to be more lax
        if "html" not in res.headers.get("Content-Type", ""):
            return res
        csp = """
        default-src 'self' 'unsafe-inline' blob:;
        img-src 'self' blob:;
        style-src 'self' 'unsafe-inline' blob:;
        frame-ancestors 'self';
        frame-src 'self' blob:;
        script-src 'self' 'unsafe-inline' 'unsafe-eval' blob:; """

        # Only enabled for debug purposes
        if True:
            csp += "report-uri http://localhost:8080/api/debug/csp-reports; "

        if request.url.path.startswith("/web/"):
            csp += "sandbox allow-scripts; "
        else:
            csp += "sandbox; "

        res.headers.add(
            # "Content-Security-Policy-Report-Only",
            "Content-Security-Policy",
            # Required to prevent aiohttp from complaining about header
            # injection
            csp.replace("\n", "")
        )
    else:
        res.headers.add(
            "Content-Security-Policy",
            "default-src 'self'; "
            "img-src 'self' blob:; "
            "style-src 'self' 'unsafe-inline' blob:; "
            "frame-ancestors 'none'; "
            "frame-src 'self' blob:; "
        )
        res.headers.merge({
            "X-Frame-Options": "DENY"
        })
    return res


