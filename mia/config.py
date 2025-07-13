import msgspec

class Server(msgspec.Struct):
    port: int

class Archive(msgspec.Struct):
    snapshot_dir: str

class Database(msgspec.Struct):
    password: str

    database: str = "mia"
    username: str = "mia"
    host: str = "localhost:5432"

class Config(msgspec.Struct):
    server: Server
    archive: Archive
    database: Database
