from ..compat import py3k
assert py3k, "this script requires python 3."

from ..profile import avg_rec_rate
from .. import util
import asyncpg
from sqlalchemy.engine import url
import asyncio
import uvloop

options = None
work_queue = None
monitor = avg_rec_rate()
connect = None


def setup(opt):
    global options
    options = opt

    db_url = url.make_url(options.dburl)

    global connect

    async def _connect(loop):
        conn = await asyncpg.connect(
            user=db_url.username,
            password=db_url.password,
            host=db_url.host,
            database=db_url.database,
            loop=loop
        )
        return conn

    connect = _connect


async def _get_connection(loop):
    return await connect(loop)


async def worker(num, loop):
    conn = await connect(loop)

    try:
        while True:
            item = await work_queue.get()
            # "row by row" means, we aren't being smart at all about
            # chunking, executemany(), or looking up groups of dependent
            # records in advance.
            if item['type'] == "geo":
                # print(
                #    "worker %d about to insert a row with logrecno %s!" %
                #    (num, item['logrecno']))
                await conn.fetch(
                    "insert into geo_record (fileid, stusab, chariter, "
                    "cifsn, logrecno) values ($1, $2, $3, $4, $5)",
                    item['fileid'], item['stusab'], item['chariter'],
                    item['cifsn'], item['logrecno']
                )
                # print(
                #    "worker %d inserted a row for logrecno %s!" %
                #    (num, item['logrecno']))
                monitor.tag(1)
            else:
                row = await conn.fetchrow(
                    "select id from geo_record where fileid=$1 and logrecno=$2",
                    item['fileid'], item['logrecno']
                )
                geo_record_id = row[0]

                rows = await conn.fetch(
                    "select d.id, d.index from dictionary_item as d "
                    "join matrix as m on d.matrix_id=m.id where m.segment_id=$1 "
                    "order by m.sortkey, d.index",
                    item['cifsn']
                )
                dictionary_ids = [row[0] for row in rows]

                assert len(dictionary_ids) == len(item['items'])

                for dictionary_id, element in zip(dictionary_ids, item['items']):
                    await conn.fetch(
                        "insert into data_element "
                        "(geo_record_id, dictionary_item_id, value) "
                        "values ($1, $2, $3)",
                        geo_record_id, dictionary_id, element
                    )
                monitor.tag(len(item['items']))
            work_queue.task_done()
    except Exception as e:
        import traceback
        traceback.print_exc()

async def run_test_async(loop):
    global work_queue
    work_queue = asyncio.Queue(loop=loop)

    tasks = []
    for i in range(options.poolsize):
        tasks.append(
            loop.create_task(worker(i, loop))
        )

    for elem, rec in enumerate(util.retrieve_geo_records()):
        await work_queue.put(rec)
        if elem % 100000 == 0:
            await work_queue.join()

    print(
        "Enqueued all geo records, waiting for "
        "all geo records to be processed")

    await work_queue.join()

    for elem, rec in enumerate(util.retrieve_file_records()):
        await work_queue.put(rec)
        if elem % 100000 == 0:
            await work_queue.join()

    print(
        "Enqueued all data records, waiting for "
        "all data records to be processed")
    await work_queue.join()

    for task in tasks:
        task.cancel()


def run_test():
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_test_async(loop))
    loop.close()
