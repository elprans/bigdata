from ..profile import Profiler
from .. import setup_db  # noqa


@Profiler.profile
def run():
    "do the thing"
    pass
