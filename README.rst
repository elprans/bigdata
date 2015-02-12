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

We here are using just two files out of the many thousands, from inside of
http://www2.census.gov/census_2000/datasets/Summary_File_1/New_York/.
The second file is also truncated to 50K lines from its original 360K
lines.   As we are INSERTing about 200 records for each of those lines,
the script is overall inserting about 1.5M rows which is plenty for us to
see how fast things are moving.

The description of these files and the data dictionary used is in a PDF at
http://www.census.gov/prod/cen2000/doc/sf1.pdf.

For the basic idea of how we're modeling this in SQL, see model.py.
SQLAlchemy is used there, but that's just to set up the tables and dictionary
data.   The performance tests use raw psycopg2 / aiopg.

Pipeline
========

The script currently uses a separate multiprocessing.Process() to read the
zip files in and parse lines into records.  The rationale here is to attempt
to remove this overhead from the test script.  However, it's not clear that
this helps, as sending the records over a multiprocessing.Queue() still
involves that the records are pickled/unpickled over a pipe, which still
takes up CPU work on the consumer side.

Run Steps
=========

Each run actually works on two different kinds of data.  First we're doing
a straight up INSERT of "geo" records.  These INSERTs are actually a little
slower because the target table has two indexes on it.   Second, we do
an INSERT of data element records; these are read in chunks of about
200 or so, and for each 200, we also need to run two SELECTs, one of which
returns 200 rows of dictionary keys for each one.   The second phase
of the run still runs way faster than the first, as these INSERTs aren't
against indexed columns.


Running It
==========

The tests run against these schemes:

* threaded, using Python 2 or Python 3
* gevent, using Python 2
* asyncio, using Python 3.

To illustrate a Python 3 run, create a virtualenv::

    python3.4 -m virtualenv /path/to/.venv

Install requirements::

    /path/to/.venv/bin/pip install -r requirements-py3k.txt

Then create a Postgresql database somewhere, and run like this::

    /path/to/.venv/bin/python -m bigdata.cmd --dburl postgresql://scott:tiger@localhost/test run row_by_row_asyncio --poolsize 50

    /path/to/.venv/bin/python -m bigdata.cmd --dburl postgresql://scott:tiger@localhost/test run row_by_row_threaded  --poolsize 50

The --poolsize attribute is basically both the number of worker coroutines or threads, as well
as the number of connections; each worker uses one persistent connection.

When its running, look at your Postgresql processes, either through psql
or just "ps -ef | grep post".   Do you see the connections?   Are they mostly "idle"
or mostly saying "SELECT" or "INSERT"?   If the former, you're not IO bound :).

How Big of a Pool Size?
------------------------

Good question.   On a Mac laptop, all the examples seem to hit their stride
at about 10-15 workers/connections.   Less than that, and there's not enough
going on to saturate the CPU.  More than that, and we're maxed on what the CPU
can do, we don't gain anything.


Results
=======

For performance results, we have three different average times.  The first
is for the geo record insert, the second is for the datafile insert
while the queue is still being filled, third is for the remaining datafile
work after the queue is done being filled.

The performance results, in order of best performers to worst, is:

* Python2 gevent  (13K r/sec, 13K r/sec, )
* Python2 threads  (6.8K r/sec, 16K r/sec, 20K r/sec)
* Python3 threads (5.2K r/sec, 13K r/sec, 18K r/sec)
* Python3 asyncio (6K recs / sec)




