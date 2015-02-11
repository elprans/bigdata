from ..profile import Profiler
from .. import setup_db  # noqa
from .. import util
import psycopg2
import queue
from sqlalchemy.engine import url
import threading

Profiler.init("row_by_row_threaded")

options = None
pool = None
work_queue = queue.Queue()
directory = None
connect = None


@Profiler.setup
def setup(opt):
    global options
    options = opt

    db_url = url.make_url(options.dburl)

    global connect

    def connect():
        conn = psycopg2.connect(
            user=db_url.username,
            password=db_url.password,
            host=db_url.host,
            dbname=db_url.database,

        )
        # async runs like this, so shall we!
        conn.autocommit = True
        return conn


def _get_connection():
    return connect()


@Profiler.profile
def row_by_row_threaded():
    "do the thing"

    for i in range(options.poolsize):
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

    for rec in util.retrieve_file_records(options.directory):
        work_queue.put(rec)


def worker():
    conn = _get_connection()
    while True:
        item = work_queue.get()
        print("item: %r" % item)
