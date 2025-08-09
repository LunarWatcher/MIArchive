from psycopg.errors import UndefinedTable
from mia.archiver.migrations import migrations
from mia.archiver.database import ArchiveDB
from pytest import raises

from mia.archiver.migrations import Migrator

def test_database_blank_state(database: ArchiveDB):
    """
    This is more of a meta test that checks for two things:
    1. That the database fixture in the test doesn't auto-upgrade
    2. That the database was successfully wiped prior to the tests running

    Failure here means something has been misconfigured, or an error left the
    test database in a live state.
    This should not happen unless there's severe errors in the migration system
    """
    with database.connect() as conn:
        with conn.cursor() as cursor:
            assert database._get_migration_version(cursor) is None

def test_migrations(database: ArchiveDB):
    """
    This tests database upgrades and downgrades. This should ensure that
    migrations remain tested in context
    """
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
                database._get_migration_version(cursor)


    with database.connect() as conn:
        with conn.cursor() as cursor:
            # We're now initialising to a blank state, so this should be empty
            migrator = Migrator(cursor)
            assert database._get_migration_version(cursor) is None

            # noop downgrades should be noop
            migrator.downgrade()

            assert database._get_migration_version(cursor) is None

def test_user_creation(udatabase: ArchiveDB):
    with udatabase.connect() as conn:
        with conn.cursor() as cursor:
            # æøå should force most hash methods to disappear the "æøå"
            password = "supersecretpasswordæøå"
            # Non-existent users are non-existent
            assert udatabase.get_user(
                cursor,
                "potato",
                password
            ) is None

            assert udatabase.create_user(
                cursor,
                "potato",
                password,
                False
            )
            user = udatabase.get_user(
                cursor,
                "potato",
                password,
            )
            assert user

            # Check that the user details match
            assert user.username == "potato"
            # Since the schema is dropped after each test, the counter should
            # also reset, so this shouldn't be a problem unless there's a
            # problem with DB wiping
            assert user.user_id == 1
            assert not user.is_admin

            # Validate that the password was hashed
            theoretically_hashed_password = cursor.execute(
                "SELECT Password FROM mia.Users WHERE Username = 'potato'"
            ).fetchone()
            assert theoretically_hashed_password is not None, \
                "If this fails, something has likely changed in the user table"
            assert theoretically_hashed_password != password, \
                "If this fails, the database is not hashing the password"
            assert "æøå" not in theoretically_hashed_password, \
                "If this fails, the database is either not hashing the " \
                "password, or the hash method has changed away from one " \
                "with a hex representation able to generate at least latin1 " \
                "in its output"
