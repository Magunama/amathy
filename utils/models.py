from datetime import datetime
from enum import Enum, IntEnum

from discord.utils import utcnow
from pony.orm import Database, Required, Optional
from pony.orm.dbapiprovider import IntConverter

db = Database()
SCHEMA_NAME = "amathy"


class EnumConverter(IntConverter):

    def validate(self, val, obj=None):
        if not isinstance(val, (Enum, int)):
            raise ValueError('Must be an Enum.  Got {}'.format(type(val)))
        return val

    def py2sql(self, val):
        return val

    def sql2py(self, value):
        # Any enum type can be used, so py_type ensures the correct one is used to create the enum instance
        return self.py_type[value]


class ReportStatus(IntEnum):
    OPEN = 0
    PENDING = 1
    COMPLETED = 2
    REJECTED = 3


class Report(db.Entity):
    _table_ = (SCHEMA_NAME, "reports")
    title = Required(str, 50, unique=True)  # maybe not unique
    description = Required(str, 500)
    author = Required(int, size=64)
    created = Required(datetime, default=utcnow())
    updated = Optional(datetime)
    status = Optional(ReportStatus, default=0)
