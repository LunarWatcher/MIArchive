import mia.config
import msgspec

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
                mia.config.Archive("./__test_snapshots/"),
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
