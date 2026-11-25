# One command per stage. The whole pipeline will be: make film
PY = .venv/bin/python

.PHONY: setup smoke validate narration radio-cut references keyframes assemble film costs

setup: ; python3 -m venv .venv && $(PY) -m pip install --upgrade pip && $(PY) -m pip install -r requirements.txt

smoke: ; $(PY) -m pipeline.smoke_test

validate: ; $(PY) -m pipeline.validate

narration: validate ; $(PY) -m pipeline.narration

radio-cut: narration ; $(PY) -m pipeline.radio_cut

references: validate ; $(PY) -m pipeline.keyframes references

keyframes: validate ; $(PY) -m pipeline.keyframes

assemble: validate ; $(PY) -m pipeline.assemble

film: validate ; $(PY) -m pipeline.narration && $(PY) -m pipeline.keyframes && $(PY) -m pipeline.assemble
costs: ; $(PY) -m pipeline.costs
