# -*- coding: utf-8; -*-

from __future__ import absolute_import, unicode_literals
import os
import unittest

from mock import Mock
from scrapy.exceptions import NotConfigured
from scrapy.settings import Settings

from scrapydatadog.extension import DatadogExtension
from scrapydatadog.settings import merge_env


class TestDatadogConfig(unittest.TestCase):

    def test_unconfigured_init(self):
        crawler = Mock()
        # don't include `DATADOG_API_KEY` and make sure it's not in the env
        os.environ.pop('DATADOG_API_KEY', None)
        crawler.settings = Settings({'DATADOG_APP_KEY': 'azertyuiop123456789'})

        with self.assertRaises(NotConfigured):
            self.extension = DatadogExtension.from_crawler(crawler)

    def test_configured_init(self):
        dd_api_key = 'azertyuiop123456789'
        dd_app_key = 'azertyuiop123456789'
        scrapy_id = '000'

        crawler = Mock()
        crawler.settings = Settings({
            'DATADOG_API_KEY': dd_api_key,
            'DATADOG_APP_KEY': dd_app_key,
            'SCRAPY_PROJECT_ID': scrapy_id,
        })

        raised = None
        try:
            DatadogExtension.from_crawler(crawler)
        except Exception as e:  # noqa
            raised = e
        self.assertIsNone(raised, 'Exception raised: {}'.format(raised))

    def test_merging_environ_in_settings(self):
        # add something that shouldn't be read
        os.environ['HELLO'] = 'world'
        # add a custom setting
        os.environ['DATADOG_HOST_NAME'] = 'localhost'
        # and a mandatory setting
        os.environ['DATADOG_API_KEY'] = 'xxxxx'
        # and a normal init + something arbitrary that should stay there
        settings = Settings({'FOO': 'bar'})

        merge_env(settings)

        self.assertEqual(settings['FOO'], 'bar')
        self.assertEqual(settings['DATADOG_HOST_NAME'], 'localhost')
        self.assertEqual(settings['DATADOG_API_KEY'], 'xxxxx')
        self.assertIsNone(settings.get('HELLO'))
