from mia.archiver.database import ArchiveDB, DBConf
from mia.archiver.migrations import Migrator, migrations
from mia.web.server import load_config
from loguru import logger

def setup_migrations(args):
    # This should be guaranteed by argparse, but doesn't hurt
    assert args.upgrade or args.downgrade
    assert not (args.upgrade and args.downgrade)

    conf = load_config()
    db = ArchiveDB(
        conf.database.database,
        conf.database.host,
        conf.database.username,
        conf.database.password,
        DBConf(
            upgrade=False,
            _allow_unupgraded=True
        )
    )

    assert args.target_version >= 0, \
        "Invalid version. Use 0 for either the latest version (--up) or to " \
        "fully downgrade (--down)"
    assert args.target_version <= len(migrations), \
        "Must specify a version in between (inclusive) 0 and (inclusive) " \
        + str(len(migrations))

    with db.connect() as conn:
        with conn.cursor() as cursor:
            curr_version = db._get_migration_version(cursor)
            logger.info("Current version is {}", curr_version)

            migrator = Migrator(cursor)
            if args.upgrade:
                migrator.upgrade(args.target_version)
            else:
                migrator.downgrade(args.target_version)
