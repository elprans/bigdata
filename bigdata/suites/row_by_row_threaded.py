from ..profile import Profiler
from .. import setup_db  # noqa


Profiler.init("row_by_row_threaded")


@Profiler.profile
def run():
    "do the thing"
    pass
