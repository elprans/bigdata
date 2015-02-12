=============
Big Data Demo
=============

Rationale
=========

When we write a program that is selecting and inserting data into a
database in Python - is it IO bound or CPU bound?   Asynchronous
advocates insist that database work is IO bound and that Python's asyncio
should make any Python program vastly more efficient than it could be
with threads.

My unconfirmed theory is that Python is way more CPU bound than people expect, and
database operations are way faster than they expect.   The additional
boilerplate of "yield from" and polling required in asyncio seems that it
would incur way more CPU overhead than just waiting for the GIL to context
switch, and this overhead falls way behind any IO lag that you'd get
from a very fast and modern database like Postgresql.

The purpose of this script is to see if in fact an asyncio situation is
vastly faster than a thread-based approach, and by how much - and then
to deeply understand why that is.    Two approaches to a data ingestion
problem are presented, using basically the identical SQL strategy.
The synchronous approach foregoes optimizations not available to the
async approach such as executemany().   We want to see if the identical
database operations run faster with async scheduling vs. threaded scheduling,
and specifically with asyncio's methodology of ``@asyncio.coroutine``,
which relies heavily upon the relatively expensive techniques of
using "yield from" calls as well as implicitly
throwing ``StopIteration`` to represent function return results.


Data Source
===========

The datafiles we are using come from the US Goverment Census 2000 dataset,
which starts at http://www2.census.gov/census_2000/datasets/.

We here are importing only a very small subset of this data, that which
falls under the category of "Summary File 1".   The description of these
files and the data dictionary used is in a PDF at
http://www.census.gov/prod/cen2000/doc/sf1.pdf.

The dataset has other "Summary File" and other categories as well, which
bear many similarities to "Summary File 1", however they are all slightly
different, and each have their own .pdf file describing their dictionaries
indivdually, e.g. sf2.pdf, sf3.pdf, etc.   There's enough data for us
just in "Summary File 1" so we're keeping it simple.

For the basic idea of how we're modeling this in SQL, see model.py.
SQLAlchemy is used there, but that's just to set up the tables and dictionary
data.   The performance tests use raw psycopg2 / aiopg.


Running It
==========

We're talking here about asyncio.  So use Python 3.4!!

Just one of the individual states in the census directory is plenty
to load this script right down.  So first get some datafiles, using
curl, wget, or whatever:

	wget -r -d 1 http://www2.census.gov/census_2000/datasets/Summary_File_1/New_York/

Then install requirements somewhere, say we have a venv:

	python3.4 -m virtualenv /path/to/.venv

Install requirements:

	/path/to/.venv/bin/pip install -r requirements.txt

Then create a Postgresql database somewhere, and run like this:

	/path/to/.venv/bin/python -m bigdata.cmd --dburl postgresql://scott:tiger@localhost/test run row_by_row_asyncio --directory /path/to/datafiles/New_York/ --poolsize 50

	/path/to/.venv/bin/python -m bigdata.cmd --dburl postgresql://scott:tiger@localhost/test run row_by_row_threaded --directory /path/to/datafiles/New_York/ --poolsize 50

The --poolsize attribute is basically both the number of worker coroutines or threads, as well
as the number of connections; each worker uses one persistent connection.

When its running, look at your Postgresql processes, either through psql
or just "ps -ef | grep post".   Do you see the connections?   Are they mostly "idle"
or mostly saying "SELECT" or "INSERT"?   If the former, you're not IO bound :).

