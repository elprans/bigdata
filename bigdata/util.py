import re
import os
import zipfile
import multiprocessing
from .compat import queue


file_queue = multiprocessing.Queue()


def retrieve_geo_records(dir_):
    if not dir_:
        raise TypeError("A directory is required")
    print("Retrieving records from %s" % dir_)
    fnames = os.listdir(dir_)
    for geo in [f for f in fnames if "geo" in f]:
        for rec in _read_file(dir_, geo, "geo"):
            yield rec


def retrieve_file_records(dir_):
    """This has to be fast too.  But TIL:

    https://twitter.com/aymericaugustin/status/565616849678008320
    "asyncio doesn't handle disk I/O, only network I/O. Apparently async
    disk I/O isn't really a thing."

    So we are using multiprocessing.

    """
    if not dir_:
        raise TypeError("A directory is required")

    print("Retrieving records from %s" % dir_)
    fnames = os.listdir(dir_)
    data_files = [
        f for f in fnames if re.match(r'^[a-z]{2}\d{5}_.{3}\.zip$', f)]

    pool = multiprocessing.Pool(2)
    work = []
    for data_file in data_files:
        work.append((dir_, data_file, "data"))
    waiter = pool.map_async(_queue_read_file, work)
    pool.close()
    while not waiter.ready():
        try:
            yield file_queue.get(False)
        except queue.Empty:
            continue


def _queue_read_file(arg):
    dir_, fname, processor_type = arg
    for rec in _read_file(dir_, fname, processor_type):
        file_queue.put(rec)


def _read_file(dir_, fname, processor_type):
    print("File %s" % fname)
    if processor_type == "geo":
        processor = _parse_geo_rec
    else:
        processor = _parse_data_rec
    for line in _unzip_lines(os.path.join(dir_, fname)):
        yield processor(line)


def _unzip_lines(fname):
    zip_ = zipfile.ZipFile(fname)
    element_name = zip_.namelist()[0]
    with zip_.open(element_name) as file_:
        for line in file_:
            yield line.decode('ascii')


def _parse_geo_rec(line):
    """

    uSF1  NY04000000  0000001122136

    """

    return dict(
        type="geo",
        fileid=line[0:6].strip(),
        stusab=line[6:8].strip(),
        chariter=line[13:16].strip(),
        cifsn=line[16:18].strip(),
        logrecno=line[18:25].strip()
    )


def _parse_data_rec(line):
    """
    uSF1,NY,000,36,0000001,337522,157698,4964,...
    """

    fields = line.strip().split(",")
    return dict(
        type="data",
        fileid=fields[0],
        stusab=fields[1],
        chariter=fields[2],
        cifsn=fields[3],
        logrecno=fields[4],
        items=fields[5:]
    )



