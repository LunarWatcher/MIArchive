# Threat model

Long story short, the threat model is to assume all archived content is potentially evil, and could access local details. Because everything is hosted under one origin, this means there's every possibility of XSS. There's two main strategies used to deal with this:

1. CSP, with `/web/` being a `sandbox`ed CSP. This does come at the risk of breaking  archived pages. No external requests are made, period, and internal requests from `/web/` must be restricted. For good measure, and (ironically) to unbreak certain pages, `/noscript/web/` also exists. It is functionally identical to `/web/`, except its `sandbox` does not have `allow-scripts`. This may or may not be more secure, so it's the preferred default.
2. CORS for non-`/web/`-pages. Auth is done with two different tokens, one of which is translated back into a header. CORS makes it possible to expose headers, which makes fetch deny access to them. Even if the sandbox is breached somehow, it has to be breached so hard that CORS can be violated, at which point we're fucked anyway.


