from sqlalchemy import Column, Integer, String, Index, ForeignKey, \
    Numeric, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class GeoRecord(Base):
    __tablename__ = 'geo_record'

    id = Column(Integer, primary_key=True)
    fileid = Column(String(6), nullable=False)
    stusab = Column(String(2), nullable=False)
    chariter = Column(String(3), nullable=False)
    cifsn = Column(String(2), nullable=False)
    logrecno = Column(String(7), nullable=False)

    # additional columns here would store the actual
    # information about geo records.

    __table_args__ = (
        Index(
            'geo_record_uq_idx',
            'fileid', 'stusab', 'chariter', 'cifsn', 'logrecno',
            unique=True
        ),
    )


class Matrix(Base):
    __tablename__ = 'matrix'

    id = Column(Integer, primary_key=True)
    code = Column(String(6), nullable=False, unique=True)
    name = Column(String(200), nullable=False)
    universe = Column(String(200), nullable=False)
    sortkey = Column(String(5), nullable=False)
    segment_id = Column(String(2), nullable=False)

    items = relationship("DictionaryItem", backref="matrix")


class DictionaryItem(Base):
    __tablename__ = 'dictionary_item'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    matrix_id = Column(ForeignKey('matrix.id'), nullable=False)
    index = Column(Integer, nullable=False)
    parent_id = Column(ForeignKey('dictionary_item.id'))

    parent = relationship("DictionaryItem", remote_side=id)

    __table_args__ = (
        UniqueConstraint('matrix_id', 'index'),
    )


class DataElement(Base):
    __tablename__ = 'data_element'

    id = Column(Integer, primary_key=True)
    geo_record_id = Column(ForeignKey('geo_record.id'), nullable=False)
    dictionary_item_id = Column(
        ForeignKey('dictionary_item.id'), nullable=False)
    value = Column(Numeric(10, 2))
