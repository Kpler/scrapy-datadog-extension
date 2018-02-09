# vim:ft=make

TARGET ?= "scrapydatadog"

lint:
	flake8 scrapydatadog

test: lint
	nosetests --verbose --with-timer \
		--with-coverage --cover-erase --cover-package=$(TARGET) \
		--with-doctest

release:
	ifndef REGISTRY
		$(error REGISTRY is not set)
	endif
	python setup.py sdist upload -r $(REGISTRY)
