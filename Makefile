install:
	python setup.py install

clean:
	rm -f src/*/*.pyc
	rm -f src/*/*/*.pyc
	rm -rf *.egg-info
	rm -rf dist/
	rm -rf build/

test: lint unittest

lint:
	@echo " >> Checking codebase with pylint"
	@pylint src/den
	@echo ""

unittest:
	@echo " >> Running testsuite"
	@PYTHONPATH=${PWD}/src nosetests ./tests/test_*.py
	@echo ""

shell:
	PYTHONPATH=${PWD}/src python
