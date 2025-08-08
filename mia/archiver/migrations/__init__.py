from loguru import logger
import psycopg
from .M001_initial import *

migrations: list[Migration] = [
    M001_Initial()
]

class Migrator:
    def __init__(self, cursor):
        assert cursor is not None

        self.cursor: psycopg.Cursor = cursor
        cursor.execute("""
        CREATE SCHEMA IF NOT EXISTS mia;
        """)
        cursor.execute("""CREATE TABLE IF NOT EXISTS mia.Migration (
            Key TEXT PRIMARY KEY,
            Version INTEGER
        )""")
        curr_version = (
            cursor.execute("SELECT Version FROM mia.Migration WHERE Key = '__mia__'")
            .fetchall()
        )
        self.curr_version: int = 0 if len(curr_version) == 0 \
            else curr_version[0][0]

    def is_updated(self):
        return self.curr_version == len(migrations)

    def upgrade(self, target: int = 0):
        """
        Upgrades to a specified version. If target == 0, the upgrade is all
        the way to the latest version.

        Warning: target is 1-indexed. target == 1 means migrations[0], etc.
        """
        if target <= 0:
            target = len(migrations)

            assert target > 0, "No migrations?"

        if self.is_updated():
            logger.info("Already up-to-date")
            return
        assert(
            self.curr_version is None
            or target > self.curr_version
        )

        for i in range(self.curr_version, target):
            logger.debug("Upgrading to v{}", i + 1)
            migrations[i].up(self.cursor)

        self._update_version(target)

    def downgrade(self, target: int = 0):
        """
        Downgrades to a specified version. if target == 0, everything is
        downgraded (equivalent to wiping the database)

        Warning: target is 1-indexed. target == 1 means migrations[0], etc.
        """
        if self.curr_version is None or self.curr_version <= 0:
            logger.error("Cannot downgrade; already at a blank state")
            return

        if target <= 0:
            target = 0

        assert target < self.curr_version, "Must be a downgrade"

        for i in range(self.curr_version, target, -1):
            logger.debug("Downgrading v{}", i)
            migrations[i - 1].down(self.cursor)

        if target != 0:
            self._update_version(target)
        else:
            logger.debug(
                "Database has been wiped (migration to v0); no version written"
            )

    def _update_version(self, target: int):
        res = self.cursor.execute(
            """
            INSERT INTO mia.Migration (Key, Version)
            VALUES ('__mia__', %s)
            ON CONFLICT (Key) DO UPDATE SET
                Version = EXCLUDED.Version;
            """,
            [ target ]
        )
        assert res.rowcount == 1, "Failed to update migration version"
