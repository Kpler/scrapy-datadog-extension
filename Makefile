# vim:ft=make

test:
	nosetests -v --with-timer --with-doctest

release:
	python setup.py sdist upload -r $(REGISTRY)
