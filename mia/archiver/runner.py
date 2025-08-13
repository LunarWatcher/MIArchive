import threading
import queue
from dataclasses import dataclass
from loguru import logger
from seleniumwire.helpers.cache import WebCache
from mia.config import Config
from mia.archiver import WebArchiver
from mia.archiver import ArchiveDB

@dataclass
class ArchiveRequest:
    url: str
    # Depth == 1 and depth == 0 are functionally identical
    # Depth == 1 means "Archive this page and everything on it"
    # Depth == 2 means the same as depth == 1, and "also archive everything
    #   linked from this page". Technically, there's no upper limit, but it's a
    #   combinatorial explosion, so it's hard-capped at 2 to avoid accidentally
    #   crawling thousands of pages from just one link
    depth: int = 1

class Runner:
    def __init__(
        self,
        database: ArchiveDB,
        config: Config
    ):
        self.database = database
        self.config = config
        self.running = True
        self._thread = threading.Thread(
            target=self._run
        )
        # Queue is thread-safe, so no mutexes needed
        self._queue = queue.Queue()
        # Used to manage the `_run` thread. This has nothing to do with
        # self._queue access - it's exclusively used to avoid busy waits
        self._cv = threading.Condition()
        self.cache = WebCache(True)

        self._callbacks = []
        self._thread.start()

    def stop(self):
        with self._cv:
            self._cv.notify_all()
        self.running = False
        self._thread.join()

    def archive(self, req: ArchiveRequest):
        self._queue.put(req)
        size = self._queue.qsize()
        with self._cv:
            self._cv.notify_all()

        return size

    def _callback(self, func):
        """
        Register a callback used for certain events on the thread. These
        functions should only be used for synchronisation in tests, and must
        not be used outside tests.
        """
        self._callbacks.append(func)

    def _run(self):
        logger.info("Archival thread started")
        """
        Internal runner function that processes archival requests. This should
        never be called by anything but the thread stored in `self._thread`
        """
        while self.running:
            if self._queue.empty():
                with self._cv:
                    for callback in self._callbacks:
                        callback({"type": "empty"})
                    self._cv.wait()

                if not self.running:
                    break
                elif self._queue.empty():
                    logger.warn(
                        "_cv.wait was triggered without a new item in the "
                        "queue. Misconfigured push?"
                    )
                    continue
            # Type predeclaration
            archive_request: ArchiveRequest
            # The queue could deal with the timeout, but dealing with that
            # manually is much better. The alternative is pushing a bogus
            # object and typechecking for it, and just, no, ew, no special
            # objects. I don't mind rawdogging condition variables
            while not self._queue.empty():
                archive_request = self._queue.get(block=False)
                logger.info(
                    "Now archiving {} with depth={}",
                    archive_request.url,
                    archive_request.depth
                )
                if archive_request.depth <= 0:
                    logger.error(
                        "Depth = 0; skipping. This should not have ended up "
                        "in the queue"
                    )
                    continue
                # TODO: the plan is to let the Archiver invoke the Runner,
                # which means the Archiver needs access to a Runner.
                # It should probably be optional for reasons.
                with WebArchiver(
                    database=self.database,
                    conf=self.config,
                    depth=archive_request.depth,
                    cache=self.cache
                ) as archiver:
                    archiver.archive(
                        archive_request.url
                    )
