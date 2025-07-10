import argparse
from mia.web import start as start_server
from mia.cli.archive import archive as archive_cli
from mia.cli.setup import setup_cli

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
server.add_argument(
    "--debug,-d",
    help = "Whether or not to enable debug mode, which adds some additional "
        "default settings not settable in any other way, as some of these are "
        "fundamentally unsafe.",
    required = False,
    action="store_true",
    default = False,
    dest = "debug",
)
server.set_defaults(func = start_server)

archive = subs.add_parser(
    "archive",
    help="Archive stuff from the command line"
)
archive.set_defaults(func = archive_cli)

setup = subs.add_parser(
    "setup",
    help="One-time environment setup of stuff needed to run MIA"
)
archive.set_defaults(func = setup_cli)

def main():
    args = parser.parse_args()
    args.func(args)
