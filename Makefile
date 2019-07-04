PHONY: clean test lint mypy pylint format isort black unittest shell
PYTHON=venv/bin/python

src/setup.py:

venv: src/setup.py
	@python3 -m venv --prompt den venv
	${PYTHON} -m pip install -U -e src/[dev]
	@touch venv

clean:
	rm -f src/*/*.pyc
	rm -f src/*/*/*.pyc
	rm -rf *.egg-info
	rm -rf dist/

test: format lint unittest

lint: pylint mypy

mypy: venv
	@echo " >> Type-checking codebase with mypy"
	@MYPYPATH=./tests/stubs ${PYTHON} -m mypy src && echo "OK"
	@echo ""

pylint: venv
	@echo " >> Checking codebase with pylint"
	@${PYTHON} -m pylint src
	@echo ""

format: isort black

isort: venv
	@echo " >> Formatting imports in codebase with isort"
	@${PYTHON} -m isort -rc src tests
	@echo ""

black: venv
	@echo " >> Formatting codebase with black"
	@${PYTHON} -m black src tests
	@echo ""

unittest: venv
	@echo " >> Running testsuite"
	@${PYTHON} -m pytest ./tests
	@echo ""

shell:
	${PYTHON}
