from ..profile import avg_rec_rate
from .. import util
import psycopg2
import queue
from sqlalchemy.engine import url
import threading

options = None
work_queue = queue.Queue()
monitor = avg_rec_rate()
connect = None


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


def worker():
    conn = _get_connection()
    cursor = conn.cursor()
    while True:
        item = work_queue.get()
        # "row by row" means, we aren't being smart at all about
        # chunking, executemany(), or looking up groups of dependent
        # records in advance.
        if item['type'] == "geo":
            cursor.execute(
                "insert into geo_record (fileid, stusab, chariter, "
                "cifsn, logrecno) values (%s, %s, %s, %s, %s)",
                (item['fileid'], item['stusab'], item['chariter'],
                 item['cifsn'], item['logrecno'])
            )
            monitor.tag(1)
        else:
            cursor.execute(
                "select id from geo_record where fileid=%s and logrecno=%s",
                (item['fileid'], item['logrecno'])
            )
            row = cursor.fetchone()
            geo_record_id = row[0]

            cursor.execute(
                "select d.id, d.index from dictionary_item as d "
                "join matrix as m on d.matrix_id=m.id where m.segment_id=%s "
                "order by m.sortkey, d.index",
                (item['cifsn'],)
            )
            dictionary_ids = [
                row[0] for row in cursor
            ]
            assert len(dictionary_ids) == len(item['items'])

            for dictionary_id, element in zip(dictionary_ids, item['items']):
                cursor.execute(
                    "insert into data_element "
                    "(geo_record_id, dictionary_item_id, value) "
                    "values (%s, %s, %s)",
                    (geo_record_id, dictionary_id, element)
                )
            monitor.tag(len(item['items']))
        work_queue.task_done()


def run_test():
    for i in range(options.poolsize):
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

    for rec in util.retrieve_geo_records(options.directory):
        work_queue.put(rec)
        monitor.report()

    print("Waiting for all geo records to be processed")
    work_queue.join()

    for rec in util.retrieve_file_records(options.directory):
        work_queue.put(rec)
        monitor.report()

