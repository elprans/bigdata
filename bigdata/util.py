import re
import os
import zipfile


def retrieve_file_records(dir_):
    if not dir_:
        raise TypeError("A directory is required")

    print("Retrieving records from %s" % dir_)
    fnames = os.listdir(dir_)
    geo_files = [f for f in fnames if "geo" in f]
    data_files = [
        f for f in fnames if re.match(r'^[a-z]{2}\d{5}_.{3}\.zip$', f)]
    for geo_file in geo_files:
        print("Geo file %s" % geo_file)
        for line in _unzip_lines(os.path.join(dir_, geo_file)):
            yield _parse_geo_rec(line)
    for data_file in data_files:
        print("Data file %s" % data_file)
        for line in _unzip_lines(os.path.join(dir_, data_file)):
            yield _parse_data_rec(line)


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
