from loguru import logger
import psycopg
from psycopg.cursor import Cursor
from .migrations import Migrator
from dataclasses import dataclass

class ArchiveRecord:
    url: str
    timestamp: str
    status_code: int

    type: str = "web"

@dataclass
class DBConf:
    upgrade: bool = True
    _allow_unupgraded: bool = False

class ArchiveDB:
    def __init__(self, dbname: str, dbhost: str, dbuser: str, dbpassword: str,
                 conf: DBConf):
        dbname = self.sanitise(dbname)
        dbhost = self.sanitise(dbhost)
        dbuser = self.sanitise(dbuser)
        dbpassword = self.sanitise(dbpassword)

        self.conf = conf
        self.connection_str = (f"dbname='{dbname}' user='{dbuser}' "
            f"password='{dbpassword}' host='{dbhost}'"
        )

        with self.connect() as conn:
            with conn.cursor() as c:
                migrator = Migrator(c)
                if not migrator.is_updated():
                    if conf.upgrade:
                        logger.debug("Running upgrade")
                        migrator.upgrade()
                    elif not conf._allow_unupgraded:
                        raise RuntimeError(
                            "You appear to be running a new CLI instance "
                            "without updating your server instance. "
                            "Please restart your server and try again"
                        )
                    else:
                        logger.warning(
                            "Skipping update; database may be inconsistent"
                        )

    def sanitise(self, a: str):
        # Per https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING-KEYWORD-VALUE
        # I think this won't be quite sufficient, but if anyone has a password
        # with not just single quotes, but backslashes immediately preceeding a
        # single quote, they're  bringing it on themselves.
        return (a
            .replace('\\', '\\\\')
            .replace("'", "\\'")
        )

    def connect(self):
        return psycopg.connect(self.connection_str)

    def _get_migration_version(self, cursor: Cursor):
        results = cursor.execute(
            "SELECT Version FROM mia.Migration WHERE Key = '__mia__'"
        ).fetchall()

        assert len(results) == 1
        return results[0][0]

