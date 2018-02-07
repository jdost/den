install:
	python setup.py install

clean:
	rm -f src/*/*.pyc
	rm -f src/*/*/*.pyc
	rm -rf *.egg-info
	rm -rf dist/
