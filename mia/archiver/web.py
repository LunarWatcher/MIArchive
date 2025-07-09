from time import sleep
from selenium.webdriver.firefox.options import Options
import seleniumwire.webdriver as sw
import seleniumwire.options as swopt
from uuid import uuid4
import json
from urllib import request
from os import path
import bs4
import requests

import zlib
import brotli

from .storage import Storage


class WebArchiver:
    GENERIC_PROCESSING_METHOD = "__default__"

    def __init__(self):
        # TODO: automate updates
        self.ublock_url = "https://github.com/gorhill/uBlock/releases/download/1.63.0/uBlock0_1.63.0.firefox.signed.xpi"
        # TODO: make configurable
        self.output_dir = "./snapshots/"
        # TODO: need some way to prevent ublock from polluting the archives
        # with requests made in the background
        # Maybe caching a profile could help?
        self.d: sw.UndetectedFirefox | None = None

        self.processing_methods = {
            "text/html": self.process_html,
            "text/": self.process_text,
            self.GENERIC_PROCESSING_METHOD: self.process_generic,
        }

    def _request(self, url: str):
        assert self.d is not None
        s = requests.Session()
        s.headers.update({
            "User-Agent": self.d.execute_script(
                "return navigator.userAgent;"
            )
        })
        for cookie in self.d.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        try:
            data = s.get(
                url,
            )

            return data
        except:
            return None

    def _init_driver(self):
        options = Options()
        options.enable_downloads = False
        options.set_preference("browser.download.folderList", 2)

        ubo_internal_uuid = f"{uuid4()}"
        options.set_preference("extensions.webextensions.uuids",
            json.dumps({"uBlock0@raymondhill.net": ubo_internal_uuid})
        )
        self.d = sw.UndetectedFirefox(
            options=options,
            seleniumwire_options=swopt.SeleniumWireOptions(
                storage_base_dir = "/tmp/.seleniumwire",
                request_storage = "memory"
            )
        )
        if not path.exists("ubo.xpi"):
            print("Missing uBlock Origin. Downloading now")
            request.urlretrieve(self.ublock_url, "ubo.xpi")
        else:
            print("Using cached uBlock Origin")

        self.ubo_id = self.d.install_addon("ubo.xpi", temporary=True)


    def text_find_urls(self, archive_url: str, body: bytes):
        return (
            body
                .replace(b"https://",
                         "{}/https://".format(archive_url).encode("utf-8"))
                .replace(b"http://",
                         "{}/https://".format(archive_url).encode("utf-8"))
        )



    def _rewrite_attr(self, parent_url: str, soup: bs4.BeautifulSoup, store, attr):
        for tag in soup.select(f"*[{attr}]"):
            if tag.attrs.get(attr) is not None:
                tag.attrs[attr] = store.url_to_archive(parent_url, tag.attrs.get(attr))

    def _rewrite_urls(self, url: str, soup: bs4.BeautifulSoup, store):
        self._rewrite_attr(url, soup, store, "href")
        self._rewrite_attr(url, soup, store, "src")


    def process_html(self, url: str, body: bytes, store: Storage):
        soup = bs4.BeautifulSoup(body, features="html.parser")
        with store.open(url, "w") as f:
            self._rewrite_urls(url, soup, store)
            f.write(str(soup))

    def process_text(self, url: str, body: bytes, store: Storage):
        with store.open(url, "wb") as f:
            f.write(
                self.text_find_urls(
                    store.webpath,
                    body
                )
            )

    def process_generic(self, url: str, body: bytes, store: Storage):
        with store.open(url, "wb") as f:
            f.write(body)

    def handleCloudflare(self):
        pass

    def __enter__(self):
        self._init_driver()
        # Allow Firefox some time to deal with startup-related downloads
        # There's some magic threshold here, but 10s seems to prevent FF from
        # polluting self.d.requests
        sleep(10)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # mostly used to make pyright stfu
        assert self.d is not None

        self.d.quit()

        self.d = None

    def _resolve_target_key(self, mimetype: str):
        if mimetype in self.processing_methods:
            return self.processing_methods[mimetype]

        prefix = mimetype.split("/", 1)[0] + "/"
        if prefix in self.processing_methods:
            return self.processing_methods[prefix]

        return self.processing_methods[self.GENERIC_PROCESSING_METHOD]

    def decode(self, body: bytes, encoding: str | None):
        if encoding == "gzip":
            return zlib.decompress(body, wbits = 16+zlib.MAX_WBITS)
        elif encoding == "br":
            return brotli.decompress(body)
        elif encoding is None:
            return body

        raise RuntimeError("Unhandled compression method: {}".format(encoding))

    def archive(self, url: str):
        assert self.d is not None, \
            "You did not run archive in a with block"

        del self.d.requests
        self.d.get(url)
        self.handleCloudflare()
        # TODO: once handle_cloudflare is implemented, there needs to be a way
        # to filter out the Cloudflare things from self.d.requests.
        # it's possible the best option is doing (pseudocode):
        # ```
        # if cloudflare_blocked and cloudflare_resolved:
        #     del self.d.requests
        #     retry_request()
        # ```

        # Allow for a few seconds for JS to process before processing the URLs
        sleep(5)

        with Storage(self.output_dir, "web") as store:
            for request in self.d.requests:
                # TODO: This does not work reliably due to rewrites from
                #   example.com -> example.com/
                # if not found and request.url != url:
                    # print("--", "skipped", request.url)
                    # continue
                # elif not found and request.url == url:
                    # found = True

                if request.response is None:
                    print("Did not get response for request to", request.url)
                    continue

                if (request.response.status_code >= 400):
                    continue

                print(request.url, "returned", request.response.status_code,
                      "and will be archived.")

                store.commit_metadata(
                    request
                )

                if (request.response.status_code < 300):
                        processing_method = self._resolve_target_key(
                            request.response.headers.get_content_type()
                        )

                        body = self.decode(
                            request.response.body,
                            request.response.headers.get("Content-Encoding")
                        )
                        try:
                            processing_method(
                                request.url,
                                body,
                                store
                            )
                        except OSError as e:
                            # 36 is filename too long
                            if e.errno == 36:
                                # TODO: figure out if there's a way to avoid
                                # long filenames in the first place
                                print("Failed to archive {}: body too long".format(request.url))
                                continue
                            else:
                                raise
