# -*- coding: utf-8 -*-

"""Scrapy extension sending crawl stats to Datadog.

## References

datadog api: http://docs.datadoghq.com/api/
stats api:   https://doc.scrapy.org/en/latest/topics/stats.html

## Scrapy built-in stats

    - downloader/request_bytes
    - downloader/request_count': 18,
    - downloader/request_method_count/GET': 4,
    - downloader/request_method_count/POST': 14,
    - downloader/response_bytes': 155010,
    - downloader/response_count': 18,
    - downloader/response_status_count/200': 18,
    - finish_reason': 'finished',
    - finish_time': datetime.datetime(2017, 4, 3, 9, 13, 46, 96057),
    - item_scraped_count': 4,
    - log_count/${level}': 29,
    - request_depth_max': 12,
    - response_received_count': 18,
    - scheduler/dequeued': 18,
    - scheduler/dequeued/memory': 18,
    - scheduler/enqueued': 18,
    - scheduler/enqueued/memory': 18,
    - start_time': datetime.datetime(2017, 4, 3, 9, 12, 20, 281530)}

## Extension built-in stats (always sent)

    - done: ping datadog (i.e. just send 1)
    - elapsed_time: time in second betwwen spider start and finish
    - exit_code: unix-like code to datadog to understand finish state

"""

import logging
import os

import datadog
from scrapy import signals
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)

# TODO make it accessible outside the extension
DEFAULT_CUSTOM_METRICS = [
    # we usually want to monitor the quantity of data found and the performance
    'item_scraped_count',
    'response_received_count',

    # logs can be a good indicator of something going wrong
    'log_count/WARNING',
    'log_count/ERROR',
]
DEFAULT_MISSING = 0
DEFAULT_DD_PREFIX = 'spider.stats'
DEFAULT_DD_HOST_NAME = 'app.scrapinghub.com'

# unix-like exit codes from Scrapy finish state conventions
# read more: http://help.scrapinghub.com/scrapy-cloud/job-outcomes
# and http://www.tldp.org/LDP/abs/html/exitcodes.html
# TODO support `close_spider_*`
EXIT_MAPPING = {'finished': 0,
                'no_reason': 0,
                'failed': 1,
                'cancelled': 130,
                'cancel_timeout': 131,
                'shutdown': 137,
                'banned': 126,
                'memusage_exceeded': 128,
                'slybot_fewitems_scraped': 2,
                'default': 1}
MANDATORY_SETTINGS = ['DATADOG_API_KEY',
                      'DATADOG_APP_KEY',
                      'SCRAPY_PROJECT_ID']


def _sanitize_metric_name(key):
    """Ensure metrics are statsd/datadog compliant, ie use lower case and
    dot-seperated namespace.

    Example:

        >>> # change nothing on good format
        >>> _sanitize_metric_name('some.metrics.name')
        'some.metrics.name'
        >>> # otherwise:
        >>> _sanitize_metric_name('SOME.weird.name')
        'some.weird.name'
        >>> _sanitize_metric_name('some/weird/name')
        'some.weird.name'

    """
    return key.lower().replace('/', '.')


def _validate_conf(conf):
    """Abort extension setup if we don't have all the required settings.

    Example:

        >>> _validate_conf({})
        Traceback (most recent call last):
            ...
        NotConfigured
        >>> _validate_conf({
        ... 'DATADOG_API_KEY': 'xxxx',
        ... 'DATADOG_APP_KEY': 'yyyy',
        ... 'SCRAPY_PROJECT_ID': '123',
        ... })
    """
    for key in MANDATORY_SETTINGS:
        if key not in conf:
            logger.warning('datadog extension setting missing: {}'.format(key))
            raise NotConfigured


def _merge_env(settings):
    """Merge settings setup from env and/or scrapy settings."""
    settings.update({
        k: v for k, v in os.environ.iteritems()
        if k in MANDATORY_SETTINGS and k not in settings
    })


def _make_list(value, sep=','):
    """Split strings around `sep` or return as is."""
    return value.split(sep) if isinstance(value, str) else value


class DatadogExtension(object):

    def __init__(self, settings, stats):
        # properly identify the job
        self.project_id = settings['SCRAPY_PROJECT_ID']

        self.dd_api_key = settings['DATADOG_API_KEY']
        self.dd_app_key = settings['DATADOG_APP_KEY']
        self.dd_host_name = settings.get('DATADOG_HOST_NAME', DEFAULT_DD_HOST_NAME)
        self.dd_metric_prefix = settings.get('DATADOG_METRICS_PREFIX', DEFAULT_DD_PREFIX)

        # extend default behaviors
        self.to_collect = _make_list(settings.get('DATADOG_CUSTOM_METRICS',
                                     DEFAULT_CUSTOM_METRICS))
        self.custom_tags = _make_list(settings.get('DATADOG_CUSTOM_TAGS', []))

        # allow the rest of the extension to access stats logic/data
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        _merge_env(crawler.settings)
        _validate_conf(crawler.settings)

        ext = cls(crawler.settings, crawler.stats)

        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        return ext

    def tags(self, spider):
        # TODO compute another tag based on spider arguments
        # (use case : some spiders split the work to avoid ban)
        return ['project:{}'.format(self.project_id),
                'spider_name:{}'.format(spider.name),
                ] + self.custom_tags

    def _metrics_fmt(self, key):
        sane_key = _sanitize_metric_name(key)
        return '{}.{}'.format(self.dd_metric_prefix, sane_key)

    def commit(self, metrics):
        # initialize API client
        logger.debug('Configure API client with credentials')
        options = {'host_name': self.dd_host_name,
                   'api_key': self.dd_api_key,
                   'app_key': self.dd_app_key}
        datadog.initialize(**options)
        logger.info('Client initialized, will now send metrics: {}'.format(metrics))

        res = datadog.api.Metric.send(metrics)
        logger.debug('API call result: {}'.format(res))

    def spider_closed(self, spider):
        # Fetch scrapy stats
        job_stats = self.stats.get_stats(spider)
        logger.debug('ScrapyStats from crawler: {}'.format(job_stats))

        # Build metrics list of dict to send to Datadog API
        tags = self.tags(spider)

        def collect(key, value):
            return {'metric': self._metrics_fmt(key),
                    'points': value,
                    'tags': tags}

        # ping datadog that a spider is done
        metrics = [collect('done', 1)]

        # notify success/failure
        exit_code = EXIT_MAPPING.get(job_stats.get('finish_reason'),
                                     EXIT_MAPPING['default'])
        metrics.append(collect('exit_code', exit_code))

        if 'finish_time' in job_stats.keys() and 'start_time' in job_stats.keys():
            elapsed_time = job_stats['finish_time'] - job_stats['start_time']
            metrics.append(collect('elapsed_time', elapsed_time.seconds))

        for key in self.to_collect:
            metrics.append(collect(key, job_stats.get(key, DEFAULT_MISSING)))

        self.commit(metrics)
