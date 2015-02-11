import re
import os
import zipfile
import multiprocessing
import queue


file_queue = multiprocessing.Queue()


def retrieve_file_records(dir_):
    """This has to be fast too.  But TIL:

    https://twitter.com/aymericaugustin/status/565616849678008320
    "asyncio doesn't handle disk I/O, only network I/O. Apparently async
    disk I/O isn't really a thing."

    """
    if not dir_:
        raise TypeError("A directory is required")

    print("Retrieving records from %s" % dir_)
    fnames = os.listdir(dir_)
    geo_files = [f for f in fnames if "geo" in f]
    data_files = [
        f for f in fnames if re.match(r'^[a-z]{2}\d{5}_.{3}\.zip$', f)]

    pool = multiprocessing.Pool(5)

    work = []

    for geo_file in geo_files:
        work.append((dir_, geo_file, "geo"))
    for data_file in data_files:
        work.append((dir_, data_file, "data"))

    waiter = pool.starmap_async(_read_file, work)
    pool.close()
    while not waiter.ready():
        try:
            yield file_queue.get(False)
        except queue.Empty:
            continue


def _read_file(dir_, fname, processor_type):
    print("File %s" % fname)
    if processor_type == "geo":
        processor = _parse_geo_rec
    else:
        processor = _parse_data_rec
    for line in _unzip_lines(os.path.join(dir_, fname)):
        rec = processor(line)
        file_queue.put(rec)


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
        fileid=line[0:6],
        stusab=line[6:8],
        chariter=line[14:17],
        cifsn=line[17:19],
        logrecno=line[19:26]
    )


def _parse_data_rec(line):
    """
    uSF1,NY,000,36,0000001,337522,157698,4964,...
    """

    fields = line.strip().split(",")
    return dict(
        fileid=fields[0],
        stusab=fields[1],
        chariter=fields[2],
        cifsn=fields[3],
        logrecno=fields[4],
        items=fields[5:]
    )
