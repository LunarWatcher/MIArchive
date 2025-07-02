import argparse
from sys import argv
from mia.web import start as start_server
from mia.cli.archive import archive as archive_cli

parser = argparse.ArgumentParser(
    prog="mia",
    description="Small archival server with anti-anti-archival features"
)

subs = parser.add_subparsers(
    required = True
)

server = subs.add_parser(
    "server",
    help="Server-related commands"
)
server.set_defaults(func = start_server)

archive = subs.add_parser(
    "archive",
    help="Archive stuff from the command line"
)
archive.set_defaults(func = archive_cli)

args = parser.parse_args()
args.func(args)

