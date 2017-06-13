# vim:ft=make

test:
	nosetests -v --with-timer

release:
	python setup.py sdist upload -r $(REGISTRY)
