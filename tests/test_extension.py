# -*- coding: utf-8; -*-
import unittest
from mock import Mock

from scrapy.exceptions import NotConfigured
from scrapydatadog.extension import DatadogExtension


class TestDatadogExtension(unittest.TestCase):

    def test_unconfigured_init(self):
        crawler = Mock()
        crawler.settings = {'SH_API_KEY': None,
                            'DATADOG_API_KEY': None,
                            'DATADOG_APP_KEY': 'azertyuiop123456789'}

        with self.assertRaises(NotConfigured):
            self.extension = DatadogExtension.from_crawler(crawler)

    def test_configured_init(self):
        sh_api_key = 'azertyuiop123456789'
        dd_api_key = 'azertyuiop123456789'
        dd_app_key = 'azertyuiop123456789'

        crawler = Mock()
        crawler.settings = {'SH_API_KEY': sh_api_key,
                            'DATADOG_API_KEY': dd_api_key,
                            'DATADOG_APP_KEY': dd_app_key}

        raised = False
        try:
            extension = DatadogExtension.from_crawler(crawler)
        except:
            raised = True
        self.assertFalse(raised, 'Exception raised')

