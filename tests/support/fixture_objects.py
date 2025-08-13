from dataclasses import dataclass

from mia.archiver.dbo.user import UserDBO

@dataclass
class MockUsers:
    standard_user: UserDBO
    alt_user: UserDBO
    admin_user: UserDBO

    # TODO: there's probably a better way to do this
    def iter(self):
        return [
            self.standard_user,
            self.alt_user,
            self.admin_user
        ]
