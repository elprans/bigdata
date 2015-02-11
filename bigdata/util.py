import re
import os


def retrieve_file_records(dir_):

    fnames = os.listdir(dir_)
    geo_files = [f for f in fnames if "geo" in f]
    data_files = [
        f for f in fnames if re.match(r'^[a-z]{2}\d{5}_.{3}\.zip$', f)]
    for geo_file in geo_files:
        for line in _unzip_lines(geo_file):
            yield _parse_geo_rec(line)
    for data_file in data_files:
        for line in _unzip_lines(data_file):
            yield _parse_data_rec(line)


def _unzip_lines(fname):
    pass


def _parse_geo_rec(line):
    pass


def _parse_data_rec(line):
    pass
