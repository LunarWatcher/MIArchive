import mia.config
import msgspec
from seleniumwire import UndetectedFirefox as UFF

def find_first(driver: UFF, host: str, port: int | None = None):
    """
    Utility function for finding the first matching request from a webdriver.
    Largely exists to deal with random stock shit polluting the requests
    object, which means none of the access objects are super reliable in
    testing.

    :param host     The host, or one of a few special keys to automatically
                    turn the host detection into a list. These keys are:
                    * "localhost" - matches "localhost:{port}", "127.0.0.1:{port}"
    :param port     The port to use when using a special host key. Has no
                    effect for most hosts; append the port to the host instead.
    """
    hosts = [host]
    if host == "localhost":
        assert port is not None

        hosts = [
            f"localhost:{port}",
            f"127.0.0.1:{port}",
        ]

    for request in driver.requests:
        if request.host in hosts:
            return request
        print(request.host)

    raise RuntimeError("Failed to find request with host=" + host)

def create_config(output: str, cfg: mia.config.Config | None = None):
    env = {}
    with open(".env.dev") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("#"):
                continue

            kv = line.split("=", maxsplit=1)
            env[kv[0]] = kv[1]

    with open(output, "wb") as f:
        if cfg is None:
            cfg = mia.config.Config(
                mia.config.Server(7001),
                mia.config.Archive("./__test_snapshots"),
                mia.config.Database(
                    # This is left as none to avoid repetition. It's injected
                    # in a sec
                    password=None
                )
            )
        cfg.database.password = env["POSTGRES_PASSWORD"]
        cfg.database.database = env["POSTGRES_DATABASE"]
        cfg.database.username = env["POSTGRES_USER"]

        f.write(msgspec.json.encode(cfg))
