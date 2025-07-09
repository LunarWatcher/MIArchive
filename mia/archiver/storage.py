from datetime import datetime, timezone
import os
import json
from urllib import parse

import seleniumwire.request
import msgspec

class Entry(msgspec.Struct):
    original_url: str
    # Where the URL redirects to. Only populated if status_code == 3xx
    redirect_target: str | None
    filepath: str
    
    mime_type: str
    status_code: int

class ArchivedWebsite(msgspec.Struct):
    # Contains per-page metadata, referring to the source URL
    pages: dict[str, Entry]


class Storage:
    def __init__(self, snapshot_dir: str,
                 type: str = "web"):
        self.timestamp = self._get_timestamp()
        self.webpath = f"/{type}/{self.timestamp}"
        self.target_directory = f"{snapshot_dir}{self.webpath}"
        self.state = ArchivedWebsite({})

        # Contains a cache of URLs in the form 
        # { "base URL": [ "url_1?args1", "url_2?args2" ] }
        # The index of each entry in the list corresponds to its postfix
        # This can be used to compute what @notation to give the files.
        self.base_urls: dict[str, list[str]] = {}

    def _get_timestamp(self):
        # TODO: I don't think I need to handle disambiguation, the number of
        # webdrivers is likely just going to be one with a queue 
        return (datetime.now(timezone.utc)
            .strftime("%Y%m%d%H%M%S%f"))

    def sanitise(self, url: str):
        # ext4 has a max filename length of 255 characters
        # A buffer of 5 allows for up to @9999 for disambiguations,
        # since the length including the @ is not considered here
        # Even this is an excessive length buffer.
        return url.replace("/", "_")[:250]

    def get_target_path(self, url: str):
        parsed = parse.urlparse(url)
        query = parsed.query
        parsed = parsed._replace(query = "")

        parsed_url = parse.urlunparse(parsed)
        if query != "":
            old_urls = self.base_urls.get(
                parsed_url,
                []
            )

            if (url in old_urls
                and (existing_idx := old_urls.index(url)) >= 0
            ):
                return os.path.join(
                    self.target_directory,
                    self.sanitise(parsed_url) + f"@{existing_idx}"
                )

            idx = len(old_urls)
            old_urls.append(url)

            self.base_urls[parsed_url] = old_urls
            parsed_url += f"@{idx}"

        return os.path.join(
            self.target_directory,
            self.sanitise(parsed_url)
        )

    def open(self, url: str, f):
        return open(self.get_target_path(url), f)

    def commit_metadata(
        self,
        request: seleniumwire.request.Request
    ):
        assert request.response is not None, \
            "You shouldn't call commit_metadata if you know your request is bad"

        src_url = request.url
        src_filename = self.get_target_path(src_url)
        src_mimetype = request.response.headers.get_content_type()
        src_code = request.response.status_code

        src_redirect = None
        if src_code >= 300 and src_code < 400:
            src_redirect = request.response.headers.get("Location")

        self.state.pages[src_url] = Entry(
            src_url,
            src_redirect,
            src_filename,
            src_mimetype,
            src_code
        )

    def url_to_archive(self, parent_url: str, url: str):
        if url.startswith(("http://", "https://")):
            # Fully qualified URL
            return f"{self.webpath}/{url}"
        elif url.startswith("javascript:"):
            # JS URLs 
            # Not sure if there are any other edge-cases beyond this and fully
            # qualified URLs where ^[^:]+: is an acceptable check
            return url
        elif url.startswith("//"):
            # Relative URL
            return f"{self.webpath}/https://{url}"

        base_url = parse.urlparse(parent_url).hostname
        if url.startswith("/"):
            # Path relative to the base domain
            return f"{self.webpath}/https://{base_url}{url}"
        else:
            # Unknown, we just assume relatiev to the parent URL.
            # It's usually relative to the parent URL's "folder" (or whatever
            # the path components are called in this context)
            return f"{self.webpath}/{parent_url}{url}"


    def __enter__(self):
        if not os.path.exists(self.target_directory):
            os.makedirs(self.target_directory)

        return self

    def __exit__(self, type, value, traceback):
        if traceback is None:
            with open(os.path.join(
                self.target_directory,
                "index.json"
            ), "wb") as f:
                f.write(msgspec.json.encode(
                    self.state
                ))

