from psycopg.cursor import Cursor
from .migration import Migration

class M001_Initial(Migration):
    def up(self, cursor: Cursor):
        cursor.execute("""
        CREATE TABLE mia.ArchiveEntries (
            Timestamp TEXT NOT NULL,
            Url TEXT NOT NULL,
            RedirectURL TEXT,
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
        cursor.execute("""
        CREATE TABLE mia.Users (
            UserID SERIAL PRIMARY KEY,
            Username TEXT NOT NULL UNIQUE,
            Password TEXT NOT NULL,
            Salt TEXT NOT NULL,
            Admin BOOLEAN NOT NULL
        );
        """)

    def down(self, cursor: Cursor):
        # Note that the schema is made prior to the migrations. The first
        # migration is special and gets away with dropping the schema, because
        # the schema is always created automagically if it doesn't exist, as a
        # prerequisite for migrations. It could be argued that this is secretly
        # a 0th migration, but I'd rather not split it out so I don't have to
        # commit after every migration.
        cursor.execute("""DROP SCHEMA mia CASCADE;""")

