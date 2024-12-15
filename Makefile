# Copyright (c) 2024 Thomas Mikalsen. Subject to the MIT License 
# rattlebox
# vim: ts=4 sw=4 
#
SHELL := /bin/bash
THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
TMP_DIR=$(THIS_DIR)tmp

.PHONY: all setup conda
all: lint test
setup: conda 
conda:
	scripts/conda-env-init environment.yml

.PHONY: lint test install clean
lint:
	mypy $(shell find rattlebox -name "*.py")
test: lint
	python -m unittest discover --pattern=*_test.py
install:
	pip install -e $(THIS_DIR)
clean:
	rm -rf $(THIS_DIR)tmp/
	rm -rf $(THIS_DIR)__pycache__/
	rm -rf $(THIS_DIR).mypy_cache
	find $(THIS_DIR) -name "*.egg-info" | xargs -r rm -rf

.PHONY: push
push:
	git add .
	sleep 1
	git commit -m "updates" . || true
	git push
