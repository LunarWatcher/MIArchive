import psycopg
from .migrations import migrations

class ArchiveRecord:
    url: str
    timestamp: str
    status_code: int

    type: str = "web"

class DBConf:
    upgrade: bool = True

class ArchiveDB:
    def __init__(self, dbname: str, dbhost: str, dbuser: str, dbpassword: str,
                 conf: DBConf):
        dbname = self.sanitise(dbname)
        dbhost = self.sanitise(dbhost)
        dbuser = self.sanitise(dbuser)
        dbpassword = self.sanitise(dbpassword)

        self.connection_str = (f"dbname='{dbname}' user='{dbuser}'"
            f"password='{dbpassword}' host='{dbhost}'"
        )

        with self.connect() as conn:
            with conn.cursor() as c:
                c.execute("""
                CREATE SCHEMA IF NOT EXISTS mia;
                """)
                c.execute("""CREATE TABLE IF NOT EXISTS mia.Migration (
                    Key TEXT PRIMARY KEY,
                    Version INTEGER PRIMARY KEY
                )""");

                curr_version = (
                    c.execute("SELECT Version FROM mia.Migration WHERE Key = '__mia__'")
                    .fetchall()
                )
                version: int = 0 if len(curr_version) == 0 else curr_version[0][0]
                if version != len(migrations):
                    if conf.upgrade:
                        for migration in migrations:
                            migration.up()
                    else:
                        raise RuntimeError(
                            "You appear to be running a new CLI instance "
                            "without updating your server instance. "
                            "Please restart your server and try again"
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


