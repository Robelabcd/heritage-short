# One command per stage. The whole pipeline will be: make film
PY = .venv/bin/python

.PHONY: setup smoke validate

setup: ; python3 -m venv .venv && $(PY) -m pip install --upgrade pip && $(PY) -m pip install -r requirements.txt

smoke: ; $(PY) -m pipeline.smoke_test

validate: ; $(PY) -m pipeline.validate
