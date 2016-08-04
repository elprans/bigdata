from ..compat import py3k
assert py3k, "this script requires python 3."

from ..profile import avg_rec_rate
from .. import util
import aiopg
from sqlalchemy.engine import url
import asyncio

options = None
work_queue = asyncio.Queue()
monitor = avg_rec_rate()
connect = None


def setup(opt):
    global options
    options = opt

    db_url = url.make_url(options.dburl)

    global connect

    @asyncio.coroutine
    def connect():
        conn = aiopg.connect(
            user=db_url.username,
            password=db_url.password,
            host=db_url.host,
            dbname=db_url.database,

        )
        return conn


def _get_connection():
    return connect()


@asyncio.coroutine
def worker(num):
    conn = yield from _get_connection()
    cursor = yield from conn.cursor()
    while True:
        item = yield from work_queue.get()
        # "row by row" means, we aren't being smart at all about
        # chunking, executemany(), or looking up groups of dependent
        # records in advance.
        if item['type'] == "geo":
            # print(
            #    "worker %d about to insert a row with logrecno %s!" %
            #    (num, item['logrecno']))
            yield from cursor.execute(
                "insert into geo_record (fileid, stusab, chariter, "
                "cifsn, logrecno) values (%s, %s, %s, %s, %s)",
                (item['fileid'], item['stusab'], item['chariter'],
                 item['cifsn'], item['logrecno'])
            )
            # print(
            #    "worker %d inserted a row for logrecno %s!" %
            #    (num, item['logrecno']))
            monitor.tag(1)
        else:
            yield from cursor.execute(
                "select id from geo_record where fileid=%s and logrecno=%s",
                (item['fileid'], item['logrecno'])
            )
            row = yield from cursor.fetchone()
            geo_record_id = row[0]

            yield from cursor.execute(
                "select d.id, d.index from dictionary_item as d "
                "join matrix as m on d.matrix_id=m.id where m.segment_id=%s "
                "order by m.sortkey, d.index",
                (item['cifsn'],)
            )
            rows = yield from cursor.fetchall()
            dictionary_ids = [row[0] for row in rows]

            assert len(dictionary_ids) == len(item['items'])

            for dictionary_id, element in zip(dictionary_ids, item['items']):
                yield from cursor.execute(
                    "insert into data_element "
                    "(geo_record_id, dictionary_item_id, value) "
                    "values (%s, %s, %s)",
                    (geo_record_id, dictionary_id, element)
                )
            monitor.tag(len(item['items']))
        work_queue.task_done()


@asyncio.coroutine
def run_test_async():
    tasks = []
    for i in range(options.poolsize):
        tasks.append(
            asyncio.async(worker(i))
        )

    for elem, rec in enumerate(util.retrieve_geo_records()):
        yield from work_queue.put(rec)
        if elem % 100000 == 0:
            yield from work_queue.join()

    print(
        "Enqueued all geo records, waiting for "
        "all geo records to be processed")

    yield from work_queue.join()

    for elem, rec in enumerate(util.retrieve_file_records()):
        yield from work_queue.put(rec)
        if elem % 100000 == 0:
            yield from work_queue.join()

    print(
        "Enqueued all data records, waiting for "
        "all data records to be processed")
    yield from work_queue.join()

    for task in tasks:
        task.cancel()


def run_test():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_test_async())
    loop.close()
