from mia import config
import msgspec
import os
from loguru import logger
from getpass import getpass

def get_bool_input(prompt):
    while True:
        res = input(f"{prompt} (y/n): ").lower()

        if res not in ["y", "yes", "n", "no"]:
            logger.error(
                f"'{res}' not valid input. Must be one of: y, n. Press CTRL-C "
                "to abort setup."
            )
            continue

        return res in ["y", "yes"]

def exec(command, conceal = None):
    """
    Thin utility wrapper around os.system that includes logging of the command
    being run.
    """
    display = command
    if conceal is not None:
        display = display.replace(
            conceal,
            "<secret hidden>"
        )
    logger.info(f"Next command: {display}")
    if conceal is not None:
        logger.info(
            "(Note that secret input has been redacted from the command "
            "output for security reasons)"
        )

    run = get_bool_input("Run this command?")
    if not run:
        raise InterruptedError(
            "Command cancelled by user; aborting setup"
        )

    os.system(
        command
    )

def setup_db(dev_setup: bool = False) -> str:
    logger.info("""The following actions will be taken:
    1. Creating a postgres user called `mia`. You will be prompted for a
        password
    2. Creating a database called `mia`
    3. Granting privileges on the newly created database to the newly created
        user.

    You will be shown each command before it's run, and asked if you want to
    execute it. Answering "no" will terminate the setup wizard, as the later
    commands assume the previous commands ahve been executed.

    If you've passed `--development` to the setup wizard, steps 2 and 3 will be
    done twice, once for `mia`, once for `miatest`, both using the same user.

    If you do read the commands, you may notice a few things:
    * Some commands may say <secret hidden>. These are passwords being redacted
        for security reasons
    * '"'"' will appear in some commands. This is because shells are shit at
        escaping single quotes:
        https://stackoverflow.com/a/1250279

        This is part of a few systems designed to avoid passwords accidentally
        breaking out of the string and being evaluated as commands. It has not
        been extensively tested, so if you plan to use many special characters
        in your input, consider not doing it.
    * If you're rerunning the setup, some commands will fail. These failures
        are ignored with the postgres commands in particular, largely to allow
        for `--development` to be passed after initially not passing it.

    If you're unsure about the commands, I recommend reading the code for this
    setup system, available here:
        https://codeberg.org/LunarWatcher/MIArchive/src/branch/master/mia/cli/setup.py

    You can also set up the database manually should you prefer. To do so,
    please press CTRL-C now, re-do the setup, and provide n when asked to
    initialise the PSQL database.

    You'll now be asked for a password to use for the new PSQL user. It will be
    copied to the config automatically.
    """)
    logger.info("Developer setup enabled: {}", dev_setup)

    password = getpass(
        "Please enter a password to use for the new Postgres user: "
    )
    escaped_password = password.replace("'", "'\"'\"'")
    exec(
        "sudo -u postgres psql -c "
        # '"'"' is necessary to properly escape the literal ' inside a ' string
        # Doing this hack in the first place means we don't need to worry about
        # several potential abuse vectors (or just general end-user problems)
        # caused by special terminal symbols not being handled correctly
        f"'CREATE USER mia WITH ENCRYPTED PASSWORD '\"'\"'{escaped_password}'\"'\"''",
        escaped_password
    )
    dbs = ["mia"]
    if dev_setup:
        dbs.append("miatest")

    for db in dbs:
        logger.info(f"Now preparing {db}")
        exec(
            f"sudo -u postgres psql -c \"CREATE DATABASE {db}\""
        )
        exec(
            f"sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE {db} TO mia\""
        )

    return password


def setup_config(dev_setup: bool):
    cfg = config.Config(
        config.Server(6996),
        config.Archive("./snapshots/"),
        config.Database(
            password = None
        )
    )

    logger.info(
        "Prepared initial config setup. Would you like help setting up the "
        "database as well? If you choose not to, you'll need to set up "
        "postgres manually. If you choose to, note that you'll be asked for "
        "your root password."
    )

    init_psql = get_bool_input("Initialise PSQL database?")
    if init_psql:
        cfg.database.password = setup_db(dev_setup)
    else:
        logger.warn(
            "PSQL setup skipped. You will need to set up the database "
            "manually, and set up the database config manually before you can "
            "use mia"
        )

    logger.info("Writing config to file...")
    with open("./config.json", "wb") as f:
        f.write(
            msgspec.json.encode(
                cfg,
            )
        )

    logger.info(
        "Done. The config file is stored in ./config.json. When running mia, "
        "make sure the working directory is set to where the config file is. "
        "You should check the config file before starting MIA. There are "
        "more config options that you don't get to change interactively, but "
        "likely want to change anyway. This includes the archive directory."
    )

    return cfg

def setup_nginx(cfg: config.Config):
    init_nginx = get_bool_input("Set up nginx?")
    if not init_nginx:
        logger.info(
            "Not setting up nginx. Do note that you should keep MIA "
            "behind some kind of reverse proxy. Other usage can and will be "
            "insecure."
        )
        return

    if not os.path.exists("/etc/nginx/"):
        logger.error("/etc/nginx does not exist. Install nginx and try again")
        return
    if not os.path.exists("/etc/nginx/conf.d"):
        logger.warn("You do not appear to have an /etc/nginx/conf.d")
        logger.warn(
            "You will be given the config to put in the right file on your own"
        )

    domain = input(
        "Enter the domain MIA will be using (ex.: archive.example.com): "
    )

    conf = f"""server {{
    listen 443 ssl http2;
    server_name {domain};
    ssl_certificate         FIXME;
    ssl_certificate_key     FIXME;

    location / {{
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   Host $host;
        proxy_pass         http://localhost:{cfg.port}/;
        proxy_redirect     http://$host/ https://$host/;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";

        # Required for HTTP basic auth services
        proxy_set_header   Authorization $http_authorization;
        proxy_pass_header  Authorization;
    }}
}}"""

    if not os.path.exists("/etc/nginx/conf.d"):
        with open("./miarchive.conf", "w") as f:
            f.write(conf)

        logger.warn(
            "Nginx config has been copied to ./miarchive.conf. You must move "
            "it to a recognised folder in your nginx setup, or copy the config "
            "into /etc/nginx/nginx.conf."
        )
    else:
        exec(f"""cat <<EOF | sudo tee /etc/nginx/conf.d/miarchive.conf
{conf}
EOF""")

        logger.info("Nginx config written to /etc/nginx/conf.d/miarchive.conf")

    logger.warn(
        "SSL config was included in the template, but no keys have "
        "been set. You just set these up yourself by editing the file"
    )

def setup_systemd():
    init_systemd = get_bool_input("Set up systemd service?")
    if not init_systemd:
        logger.warn("Not setting up systemd. Server won't start automatically")
        return

    file = """[Unit]
Description=Self-hosted archival utility
Wants=network-online.target
After=network.target

[Service]
Restart=on-failure
RestartSec=60s
Type=idle
WorkingDirectory=/opt/miarchive
ExecStart=/opt/miarchive/env/bin/mia server
User=jade

[Install]
WantedBy=multi-user.target
"""

    exec(f"""cat <<EOF | sudo tee /etc/systemd/system/miarchive.service
{file}
EOF""")

def setup_cli(args):
    print("""┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃Welcome to the MIArchive setup wizard┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛""")
    cfg = setup_config(
        args.dev_setup
    )
    setup_nginx(cfg)
    setup_systemd()
