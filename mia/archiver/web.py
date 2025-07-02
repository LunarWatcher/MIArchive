from selenium.webdriver.firefox.options import Options
import undetected_geckodriver as ud
from uuid import uuid4
import json
from urllib import request
from os import path
import bs4
import requests

from .storage import Storage

class WebArchiver:
    def __init__(self):
        # TODO: automate updates
        self.ublock_url = "https://github.com/gorhill/uBlock/releases/download/1.63.0/uBlock0_1.63.0.firefox.signed.xpi"
        # TODO: make dynamic
        self.output_dir = "./snapshots/"
        self._init_driver()

    def _request(self, url: str):
        s = requests.Session()
        s.headers.update({
            "User-Agent": self.d.execute_script(
                "return navigator.userAgent;"
            )
        })
        for cookie in self.d.get_cookies():
            s.cookies.set(cookie['name'], cookie['value'], domain=cookie['domain'])
        try:
            data = requests.get(
                url,
                headers = {
                    "User-Agent": self.d.execute_script(
                        "return navigator.userAgent;"
                    )
                },
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
        self.d = ud.Firefox(
            options=options
        )
        if not path.exists("ubo.xpi"):
            print("Missing uBlock Origin. Downloading now")
            request.urlretrieve(self.ublock_url, "ubo.xpi")
        else:
            print("Using cached uBlock Origin")

        self.ubo_id = self.d.install_addon("ubo.xpi", temporary=True)

    def _naive_find(self, selector, attr, soup, store):
        for tag in soup.select(selector):
            link = tag.attrs.get(attr)
            if link is not None and link != "":
                data = self._request(link)
                if data is None or data.status_code >= 400:
                    continue
                with store.open(link, "w") as f:
                    f.write(data.text)
            else:
                # TODO: log error
                pass

    def _archive_images(self, soup, store):
        for tag in soup.select("img[src]"):
            link = tag.attrs.get("src")
            print(link)
            if link is not None and link != "":
                data = self._request(link)
                if data is None or data.status_code >= 400:
                    continue
                with store.open(link, "wb") as f:
                    f.write(data.content)

    def _archive_scripts(self, soup, store):
        self._naive_find("script[src]", "src", soup, store)

    def _archive_stylesheets(self, soup, store):
        self._naive_find("link[type='text/css']", "href", soup, store)

    def _rewrite_attr(self, parent_url: str, soup: bs4.BeautifulSoup, store, attr):
        for tag in soup.select(f"*[{attr}]"):
            if tag.attrs.get(attr) is not None:
                tag.attrs[attr] = store.url_to_archive(parent_url, tag.attrs.get(attr))

    def _rewrite_urls(self, url: str, soup: bs4.BeautifulSoup, store):
        self._rewrite_attr(url, soup, store, "href")
        self._rewrite_attr(url, soup, store, "src")


    def sanitiseAndSave(self, url, html):
        soup = bs4.BeautifulSoup(html, features="html.parser")
        with Storage(self.output_dir, "web") as store:
            self._archive_images(soup, store)
            self._archive_scripts(soup, store)
            self._archive_stylesheets(soup, store)

            with store.open(url, "w") as f:
                self._rewrite_urls(url, soup, store)
                f.write(str(soup))



    def handleCloudflare(self):
        pass

    def archive(self, url: str):
        self.d.get(url)
        self.handleCloudflare()
        self.sanitiseAndSave(url, self.d.page_source)
