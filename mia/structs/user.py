from msgspec import Struct

class User(Struct):
    username: str
    user_id: int
    is_admin: bool
