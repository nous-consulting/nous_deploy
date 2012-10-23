#!/usr/bin/make
#
# Makefile for nous_deploy Sandbox
#

BOOTSTRAP_PYTHON=python2.6
TIMEOUT=3
BUILDOUT_OPTIONS=
BUILDOUT = bin/buildout -t $(TIMEOUT) $(BUILDOUT_OPTIONS) && touch bin/*

export LC_ALL := en_US.utf8

.PHONY: all
all: python/bin/python bin/buildout bin/fab

python/bin/python:
	$(BOOTSTRAP_PYTHON) virtualenv.py --no-site-packages python

bin/buildout: python/bin/python
	$(MAKE) bootstrap

bin/fab: buildout.cfg bin/buildout setup.py versions.cfg
	$(BUILDOUT)

.PHONY: bootstrap
bootstrap: python/bin/python
	python/bin/python bootstrap.py

.PHONY: buildout
buildout:
	$(BUILDOUT)
