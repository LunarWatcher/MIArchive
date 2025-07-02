import psycopg
from .migrations import migrations

class ArchiveRecord:
    url: str
    timestamp: str
    status_code: int

    type: str = "web"

class ArchiveDB:
    def __init__(self, dbname: str, dbhost: str, dbuser: str, dbpassword: str):
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
                    for migration in migrations:
                        migration.up()

    

    def sanitise(self, a: str):
        # Per https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING-KEYWORD-VALUE
        return (a
            .replace('\\', '\\\\')
            .replace("'", "\\'")
        )

    def connect(self):
        return psycopg.connect(self.connection_str)


