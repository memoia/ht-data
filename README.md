Data Import/Export Code Challenge
=================================

Requirements: GNU Make, Python 2.7


Getting started
---------------

Set up project and run tests:

* ``make install test``

Review command-line arguments using the `-h` switch,
via any of the command aliases, like so:

* ``./dbexport -h``

It would have been better to use pipes for reading
from the database fixture, and subsequently exporting
and re-importing. Using the table name as an identifier
for every invocation can get confusing. Maybe next time.
To "dump" the standard fixture, invoke:

* ``./dbexport -t fixtures/standard``

This will write a file to `output/out_export_standard`.

To then "load" the exported data, invoke:

* ``./dbimport -t fixtures/standard``

This writes to the path `output/out_import_standard`.

Thus, to compare the original data set with the result, use:

* ``diff fixtures/standard output/out_import_standard``

Please see fixtures/README.markdown for descriptions of fixtures.


Scenarios I considered
----------------------

* Standard "happy path": Does it work when there are no
  funny characters in any of the fields?
* Alternate field separators: Does it work when we use
  different delimiters for fields in source files, and
  when we specify those delimiters as arguments?
* Alternate row separators: Does it work when we use
  different delimiters for rows in source files, and
  when we specify those delimiters as arguments?
* Records containing field separators within a field:
  When a field uses a quoted format, do we properly
  escape delimiters rather than translating them to
  our internal format?
* Records with backslashes: Do we properly escape
  backslashes in records? In the case of records beginning
  or ending with backslashes, do we ensure that they
  are preserved?
* Records containing internal delimiters: Do we properly
  escape records that use our internal delimiters? Do we
  handle these properly alongside backslashes?
