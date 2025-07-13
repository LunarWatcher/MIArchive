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
        cursor.execute("""
        CREATE TABLE mia.Users (
            UserID SERIAL PRIMARY KEY,
            Username TEXT NOT NULL UNIQUE,
            Password TEXT NOT NULL,
            Admin BOOLEAN NOT NULL
        );
        INSERT INTO mia.Users (Username, Password, Admin)
        VALUES ('admin', 'admin', true);
        """)

    def down(self, cursor: Cursor):
        cursor.execute("""DROP SCHEMA mia CASACADE;""")

