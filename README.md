Data Import/Export Code Challenge
=================================

Requirements: GNU Make, Python 2.7

``make install``

``./dbexport -h``

``./dbexport -t fixtures/standard``
``./dbimport -t fixtures/standard``
``diff fixtures/standard output/out_import_standard``
