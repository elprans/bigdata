import re
import os
import zipfile
import multiprocessing
from .compat import queue

work_queue = multiprocessing.Queue()

dir_ = os.path.join(os.path.dirname(__file__), "..", "data")


def retrieve_geo_records():
    print("Retrieving records from %s" % dir_)
    fnames = os.listdir(dir_)
    for geo in [f for f in fnames if "geo" in f]:
        for rec in _read_file_multiprocessing(dir_, geo, "geo"):
            yield rec


def retrieve_file_records():
    print("Retrieving records from %s" % dir_)
    fnames = os.listdir(dir_)
    for data_file in [
        f for f in fnames if re.match(r'^[a-z]{2}\d{5}.*\..{3}\.zip$', f)
    ]:
        for rec in _read_file_multiprocessing(dir_, data_file, "data"):
            yield rec


def _read_file_multiprocessing(dir_, fname, processor_type):
    process = multiprocessing.Process(
        target=_read_file_process, args=(dir_, fname, processor_type))
    process.start()

    while process.is_alive():
        try:
            yield work_queue.get(False)
        except queue.Empty:
            continue


def _read_file_process(dir_, fname, processor_type):
    print("File %s" % fname)
    if processor_type == "geo":
        processor = _parse_geo_rec
    else:
        processor = _parse_data_rec
    for line in _unzip_lines(os.path.join(dir_, fname)):
        rec = processor(line)
        work_queue.put(rec)


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



