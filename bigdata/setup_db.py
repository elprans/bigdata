from sqlalchemy import create_engine
from sqlalchemy.orm import Session
import json
import os

from . import model

data = os.path.join(os.path.dirname(__file__), "..", "data")
engine = None


def initdb(engine):
    sess = Session(engine)

    segments = json.load(os.path.join(data, "segments.json"))
    dictionary = json.load(os.path.join(data, "dictionary.json"))

    for matrix_rec in dictionary:
        code = matrix_rec["code"]
        segment_id = segments[0]["segment"]
        if code == segments[0]["ending_matrix"]:
            segments.pop(0)

        matrix = model.Matrix(
            name=matrix_rec["name"],
            code=code,
            universe=matrix_rec["universe"],
            segment_id=segment_id
        )

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
                stack.append((entry["elements"], dictionary_item))

        sess.flush()

    sess.commit()

from .profile import Profiler


@Profiler.setup_once
def setup_database(dburl, echo):
    global engine
    engine = create_engine(dburl, echo=echo)
    model.Base.metadata.create_all(engine)
    initdb(engine)


@Profiler.setup_once
def clear_data(dburl, echo):
    with engine.begin() as conn:
        conn.execute(
            model.DataElement.__table__.delete()
        )
        conn.execute(
            model.GeoRecord.__table__.delete()
        )
