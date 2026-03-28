PYTHON ?= python3

.PHONY: test run seed

test:
	$(PYTHON) -m unittest discover -s tests -v

run:
	$(PYTHON) -m uvicorn oh_my_gtm.api.app:app --reload

seed:
	$(PYTHON) scripts/seed_demo.py
