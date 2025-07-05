from psycopg.cursor import Cursor
from .migration import Migration

class M001_Initial(Migration):
    def up(self, cursor: Cursor):
        cursor.execute("""
        CREATE TABLE mia.ArchiveEntries (
            Timestamp TEXT NOT NULL,
            Url TEXT NOT NULL,
            MimeType TEXT NOT NULL,
            HttpCode INTEGER NOT NULL,
            PRIMARY KEY(Timestamp, Url)
        );
        CREATE INDEX timestamp_listing ON mia.ArchiveEntries (
            Timestamp
        );
        CREATE INDEX url_listing ON mia.ArchiveEntries (
            Url
        );
        """)

    def down(self, cursor: Cursor):
        cursor.execute("""DROP SCHEMA mia CASACADE;""")

