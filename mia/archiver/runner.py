import threading
import queue
from dataclasses import dataclass
from loguru import logger
from mia.config import Config
from mia.archiver import WebArchiver

@dataclass
class ArchiveRequest:
    url: str
    # Depth == 1 and depth == 0 are functionally identical
    # Depth == 1 means "Archive this page and everything on it"
    # Depth == 2 means the same as depth == 1, and "also archive everything
    #   linked from this page"
    depth: int = 1

class Runner:
    def __init__(self, config: Config):
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

    def _run(self):
        logger.info("Archival thread started")
        """
        Internal runner function that processes archival requests. This should
        never be called by anything but the thread stored in `self._thread`
        """
        while self.running:
            if self._queue.empty():
                with self._cv:
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
                # TODO: the plan is to let the Archiver invoke the Runner,
                # which means the Archiver needs access to a Runner.
                # It should probably be optional for reasons.
                with WebArchiver(
                    depth = archive_request.depth
                ) as archiver:
                    archiver.archive(
                        archive_request.url
                    )
