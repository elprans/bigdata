=============
Big Data Demo
=============

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