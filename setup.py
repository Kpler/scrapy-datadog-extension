# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils import setup

import scrapydatadog


packages = [
    'scrapydatadog',
]

requires = [
    'scrapy',
    'datadog',
]

setup(
    name='scrapydatadog',
    version=scrapydatadog.__version__,
    description='Scrapy extension to send scrapy stats to Datadog.',
    author='Kpler Engineering',
    author_email='dev@kpler.com',
    url='http://github.com/kpler/scrapy-datadog-extension',
    packages=packages,
    install_requires=requires,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
    ),
)
