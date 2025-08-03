from psycopg.errors import UndefinedTable
from mia.archiver.migrations import migrations
from mia.archiver.database import ArchiveDB
from pytest import raises

from mia.archiver.migrations import Migrator

def test_database_blank_state(database: ArchiveDB):
    with database.connect() as conn:
        with conn.cursor() as cursor:
            with raises(Exception):
                database._get_migration_version(cursor)

def test_migrations(database: ArchiveDB):
    # The Migrator never updates its internal version, so each call that
    # changes the version needs to be separate for this test to work
    with database.connect() as conn:
        with conn.cursor() as cursor:
            migrator = Migrator(cursor)
            migrator.upgrade()

            assert database._get_migration_version(cursor) \
                == len(migrations)

    with database.connect() as conn:
        with conn.cursor() as cursor:
            migrator = Migrator(cursor)
            migrator.downgrade()
            conn.commit()
            with raises(UndefinedTable):
                assert database._get_migration_version(cursor) \
                    == 0


    with database.connect() as conn:
        with conn.cursor() as cursor:
            migrator = Migrator(cursor)
            # The Migrator reinitialises the migration table, so this should
            # now exist again
            # But because no data is in the table, it should raise an
            # AssertionError
            with raises(AssertionError):
                assert database._get_migration_version(cursor) \
                    == 0
            # noop downgrades should be noop
            migrator.downgrade()
            with raises(AssertionError):
                assert database._get_migration_version(cursor) \
                    == 0

