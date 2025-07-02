from abc import abstractmethod

from psycopg.cursor import Cursor


class Migration():
    @abstractmethod
    def up(self, cursor: Cursor):
        pass

    @abstractmethod
    def down(self, cursor: Cursor):
        pass

