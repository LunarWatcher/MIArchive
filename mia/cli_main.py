import argparse
from mia.web import start as start_server
from mia.cli.archive import archive as archive_cli
from mia.cli.setup import setup_cli

parser = argparse.ArgumentParser(
    prog="mia",
    description="Small archival server with anti-anti-archival features"
)

subs = parser.add_subparsers(
    required=True,
)

server = subs.add_parser(
    "server",
    help="Server-related commands"
)
server.add_argument(
    "-d", "--debug",
    help="Whether or not to enable debug mode, which adds some additional "
        "default settings not settable in any other way, as some of these are "
        "fundamentally unsafe.",
    required=False,
    action="store_true",
    default=False,
    dest="debug",
)
server.add_argument(
    "-s", "--headed",
    help="Pass to disable automatically starting xvfb. If you're running headlessly, "
        "this will result in hard failures.",
    required=False,
    default=True,
    action="store_false",
    dest="headed"
)
server.set_defaults(func = start_server)

archive = subs.add_parser(
    "archive",
    help="Archive stuff from the command line"
)
archive.add_argument(
    "-s", "--headed",
    help="Pass to disable automatically starting xvfb. If you're running headlessly, "
        "this will result in hard failures.",
    required=False,
    default=True,
    action="store_false",
    dest="headed"
)
archive.set_defaults(func = archive_cli)

setup = subs.add_parser(
    "setup",
    help="One-time environment setup of stuff needed to run MIA"
)
setup.add_argument(
    "-d", "--developer",
    help="Whether or not to also enable development setup features. You "
        "should only supply this if you plan to develop MIArchive itself, as "
        "some of the setup commands are required for testing to work",
    required=False,
    default=False,
    action="store_true",
    dest="dev_setup"
)
setup.set_defaults(func = setup_cli)

def main():
    args = parser.parse_args()
    args.func(args)
