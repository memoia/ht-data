SHELL := /bin/bash
PYTHON := $(shell which python2.7)
MANAGE := $(CURDIR)/dbmanage.py

.PHONY: install clean test

test: install
	$(PYTHON) $(MANAGE)

$(CURDIR)/dbexport $(CURDIR)/dbimport:
	ln -s $(MANAGE) $@

install: $(CURDIR)/dbexport $(CURDIR)/dbimport

clean:
	rm -f $(CURDIR)/dbexport $(CURDIR)/dbimport $(CURDIR)/output/out_*
