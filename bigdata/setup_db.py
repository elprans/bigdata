from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import json
import os
import itertools

from . import model

data = os.path.join(os.path.dirname(__file__), "..", "data")
engine = None


def initdb(engine):
    sess = Session(engine)

    segments = json.load(open(os.path.join(data, "segments.json")))
    dictionary = json.load(open(os.path.join(data, "dictionary.json")))

    counter = itertools.count(1)

    for matrix_rec in dictionary:
        code = matrix_rec["code"]
        segment_id = segments[0]["segment"]
        if code == segments[0]["ending_matrix"]:
            segments.pop(0)

        matrix = model.Matrix(
            name=matrix_rec["name"],
            code=code,
            universe=matrix_rec["universe"],
            segment_id=segment_id,
            sortkey="%.5d" % next(counter)
        )
        print("Matrix: %s" % code)
        sess.add(matrix)

        stack = []
        stack.insert(0, (matrix_rec["elements"], None))
        while stack:
            collection, parent = stack.pop(0)
            for entry in collection:
                dictionary_item = model.DictionaryItem(
                    matrix=matrix,
                    name=entry["name"],
                    index=entry["index"],
                    parent=parent
                )
                sess.add(dictionary_item)
                if "elements" in entry:
                    stack.append((entry["elements"], dictionary_item))

        sess.flush()

    sess.commit()


def setup_database(options, drop=False):
    global engine
    engine = create_engine(options.dburl, echo=options.echo)
    if drop:
        model.Base.metadata.drop_all(engine)
    if not engine.has_table(model.DataElement.__table__):
        print("Database seems to be empty, creating tables")
        model.Base.metadata.create_all(engine)
        print("Loading dictionary data...")
        initdb(engine)


def clear_data(options):
    with engine.begin() as conn:
        # faster than DELETE

        model.DataElement.__table__.drop(conn)
        model.GeoRecord.__table__.drop(conn)

        model.GeoRecord.__table__.create(conn)
        model.DataElement.__table__.create(conn)
