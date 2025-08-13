from dataclasses import dataclass

@dataclass
class UserDBO:
    username: str
    password: str
    admin: bool
