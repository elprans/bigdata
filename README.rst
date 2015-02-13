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

Transactions / Executemany
==========================

psycopg2's async system removes psycopg2's ability to run in non-autocommit mode,
that is, there is no BEGIN/COMMIT emitted by psycopg2 automatically.  aiopg
provides no workaround for this, even though this would be very possible.
Using autocommit makes single-statement operations a markedly faster, which
is a factor to consider when benching async vs. non-async, while
using it for multi-statement operations has less of an impact.
An explcicit transaction surrounding multiple statements grants possibly a
5% speed bump in the second part of this test suite, where we are sending
blocks of INSERT statements; to experiment with that, use the
``--no-autocommit`` flag, currently only implemented for the "threaded"
suite.

Another missing feature from psycopg2's async is support for DBAPI
``executemany()``.  This feature allows a large set of parameters to be
run very efficiently with only a single statement invocation.  The DBAPI
may choose to make use of a prepared statement to make this more efficient,
or in the case of psycopg2, it takes advantage of the fact that it uses
blazingly-fast C code to run the multiple statements.  aiopg could also easily
implement compatibility for this feature, however chooses not to.

The "threaded" suite can make use of ``executemany()`` for one particular
series of INSERT statements using the ``--allow-executemany`` flag.  This
flag should be combined with ``--no-autocommit`` for best results.
Using these two flags, a local run on the Mac Book Pro achieves approximately
22K rec/sec on Py3k and 26K rec/sec on Py2K for the second part of the test.
This is a modest improvement, though not enough to highlight within most
of our results which stick with everyone using autocommit, single execute().


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
at about 10-15 workers/connections.    On my Lenovo Thinkpad running Fedora,
hitting a local database I'm able to push it way up to 350 workers/connections
(!) before it maxes out (yes, 350 threads still outperforms 350 asyncio coroutines, which
seems...surprising!), and running over a network to a remote Postgresql, 120
seemed to work best.

The "sweet spot" here is that where we can totally saturate the local CPU
with enough work to be occupied the vast majority of the time.   This was
fully possible in all scenarios, including PG over the network.


Results
=======

For performance results, we have three different average times.  The first
is for the geo record insert, the second is for the datafile insert
while the queue is still being filled, third is for the remaining datafile
work after the queue is done being filled.   Where the second value is
N/A means the work queue filled up before any meaningful work could
be performed against the database.

Each series of tests is ordered by best performer in the third category;
as this represents the most "pure" usage of the paradigm as there's
no queueing in the background going on.

Using two machines, we get the best results when Python runs on one
of them and the database on another; an early indicator of CPU power being
more of a factor than network overhead.  Both machines are very powerful
laptops with 32G of ram each.


MAC BOOK PRO w/ OSX - LOCAL POSTGRESQL 9.4
------------------------------------------

- 15 processes/connections

* Python2.7.5 threads  (6.8K r/sec, 16K r/sec, 20K r/sec)
* Python3.4.2 threads (5.5K r/sec, 14K r/sec, 19K r/sec)
* Python2.7.5 gevent  (9K r/sec, 9K r/sec, 13K r/sec)
* Python3.4.2 asyncio (5K r/sec, 5K r/sec, 6K r/sec)

LENOVO THINKPAD w/ FEDORA 21 - LOCAL POSTGRESQL 9.3.5
-----------------------------------------------------

On this environment, we did in fact begin to see the theoretical
advantage of async approaches taking a little bit of effect, in that
we could ramp the concurrent number of processes very high, which is
of course when threads become more expensive.  This allowed gevent to
slightly outperform threads, but Python3's asyncio with its very heavy
in-Python overhead, still dead last.

- 350 processes/connections

* Python2.7.8 gevent (13k r/sec, N/A, 9k r/sec)
* Python2.7.8 threads (11k r/sec, N/A, 9k r/sec)
* Python3.4.1 threads (9k r/sec, N/A, 9k r/sec)
* Python3.4.1 asyncio (7k r/sec, N/A, 6k r/sec)

- 150 processes/connections

* Python2.7.8 threads (8k r/sec, N/A, 7k r/sec)
* Python3.4.1 threads (8k r/sec, N/A, 6.5K r/sec)
* Python2.7.8 gevent (7k r/sec, N/A, 6k r/sec)
* Python3.4.1 asyncio (6k r/sec, N/A, 5.5k r/sec)

LENOVO THINKPAD w/ FEDORA 21 - NETWORK TO MAC BOOK PRO W/ POSTGRESQL 9.4
-------------------------------------------------------------------------

Trying to get PG to be more IO-heavy, I had the thinkpad run as many connections
as it could over the network to the PG database running on the Mac.  I was able
to run as many as 280 processes/connections with asyncio, but not as many
with threads; here's where we also get into one of the theoretical benefits
of async, that you can run lots of processes.  This is true!  However,
the "sweet spot" here was about 120 connections in any case.

- 120 processes/connections

* Python2.7.8 threads (22k r/sec, N/A, 22k r/sec)
* Python3.4.1 threads (10k r/sec, N/A, 21k r/sec)
* Python2.7.8 gevent (18k r/sec, N/A, 19k r/sec)
* Python3.4.1 asyncio (8k r/sec, N/A, 10k r/sec)


