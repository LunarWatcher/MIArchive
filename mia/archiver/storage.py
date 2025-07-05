from datetime import datetime, timezone
import os
from urllib import parse

class Storage:
    def __init__(self, snapshot_dir: str,
                 type: str = "web"):
        timestamp = self._get_timestamp()
        self.webpath = f"/{type}/{timestamp}"
        self.target_directory = f"{snapshot_dir}{self.webpath}"
        pass

    def _get_timestamp(self):
        # TODO: I don't think I need to handle disambiguation, the number of
        # webdrivers is likely just going to be one with a queue 
        return (datetime.now(timezone.utc)
            .strftime("%Y%m%d%H%M%S%f"))

    def sanitise(self, url: str):
        return url.replace("/", "_")

    def get_target_path(self, url: str):
        return os.path.join(
            self.target_directory,
            self.sanitise(url)
        )

    def open(self, url: str, f):
        return open(self.get_target_path(url), f)

    def url_to_archive(self, parent_url: str, url: str):
        if url.startswith("http://") or url.startswith("https://"):
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
        pass
