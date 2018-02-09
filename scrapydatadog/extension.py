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
from datadog.api.constants import CheckStatus
from scrapy import signals
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)

# define sane default behavior of the extension
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
DEFAULT_SERVICE_CHECK = 'data.is_sourced'
MANDATORY_SETTINGS = [
    'DATADOG_API_KEY',
    'DATADOG_APP_KEY',
    'SCRAPY_PROJECT_ID',
]
CUSTOM_SETTINGS = [
    'DATADOG_HOST_NAME',
    'DATADOG_METRICS_PREFIX',
    'DATADOG_SERVICE_CHECK',
    'DATADOG_CUSTOM_METRICS',
    'DATADOG_CUSTOM_TAGS',
]

# read more: http://help.scrapinghub.com/scrapy-cloud/job-outcomes
# TODO support `close_spider_*`
DD_STATUS_MAPPING = {
    'finished': CheckStatus.OK,
    'no_reason': CheckStatus.UNKNOWN,
    'failed': CheckStatus.CRITICAL,
    'cancelled': CheckStatus.WARNING,
    'cancel_timeout': CheckStatus.CRITICAL,
    'shutdown': CheckStatus.CRITICAL,
    'banned': CheckStatus.CRITICAL,
    'memusage_exceeded': CheckStatus.CRITICAL,
    'slybot_fewitems_scraped': CheckStatus.WARNING,
    'default': CheckStatus.UNKNOWN,
}


def _sanitize_metric_name(key):
    """Ensure metrics are statsd/datadog compliant, ie use lower case and
    dot-seperated namespace.

    Examples:
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
            logger.warning('datadog extension mandatory setting missing: {}'.format(key))
            logger.warning('scraper will go on but extension will be disabled.')
            raise NotConfigured


def _merge_env(settings):
    """Merge settings setup from env and/or scrapy settings.

    Note that Scrapy `settings` take precedence over env and won't be modified
    if already set.

    Also, this method doesn't return anything. Instead it mutates the
    given dict on purpose.

    """
    ALL_SETTINGS = MANDATORY_SETTINGS + CUSTOM_SETTINGS

    settings.update({
        k: v for k, v in os.environ.iteritems()
        if k in ALL_SETTINGS and k not in settings
    })


def _make_list(value, sep=','):
    """Split strings around `sep` or return as is.

    Examples:
        >>> _make_list('foo,bar')
        ['foo', 'bar']
        >>> _make_list('foo,bar', sep='.')
        ['foo,bar']
        >>> _make_list(3)
        3

    """
    return value.split(sep) if isinstance(value, str) else value


class DatadogExtension(object):

    def __init__(self, settings, stats):
        # properly identify the job
        self.project_id = settings['SCRAPY_PROJECT_ID']

        self.dd_api_key = settings['DATADOG_API_KEY']
        self.dd_app_key = settings['DATADOG_APP_KEY']
        self.dd_host_name = settings.get('DATADOG_HOST_NAME', DEFAULT_DD_HOST_NAME)
        self.dd_metric_prefix = settings.get('DATADOG_METRICS_PREFIX', DEFAULT_DD_PREFIX)
        self.dd_service_check = settings.get('DATADOG_SERVICE_CHECK', DEFAULT_SERVICE_CHECK)

        # extend default behaviors
        self.to_collect = _make_list(settings.get('DATADOG_CUSTOM_METRICS', DEFAULT_CUSTOM_METRICS))
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
        res = datadog.api.Metric.send(metrics)
        logger.debug('API call result: {}'.format(res))

    def publish_status(self, spider_name, finish_reason, tags):
        status = DD_STATUS_MAPPING.get(finish_reason)
        msg = 'Spider {} ended because: {}'.format(spider_name, finish_reason)

        datadog.api.ServiceCheck.check(check=self.dd_service_check,
                                       status=status,
                                       message=msg,
                                       host=DEFAULT_DD_HOST_NAME,
                                       tags=tags)

    def spider_closed(self, spider):
        # initialize API client
        logger.info('connecting to datadgo API')
        options = {
            'api_key': self.dd_api_key,
            'app_key': self.dd_app_key,
        }
        datadog.initialize(**options)

        # Fetch scrapy stats
        job_stats = self.stats.get_stats(spider)
        logger.debug('ScrapyStats from crawler: {}'.format(job_stats))

        # Build metrics list of dict to send to Datadog API
        tags = self.tags(spider)

        def collect(key, value):
            """Format intuitive key=value into datadog format.

            ref: http://datadogpy.readthedocs.io/en/latest/#datadog.api.Metric.send

            """
            return {
                'metric': self._metrics_fmt(key),
                'points': value,
                'tags': tags,
                'host': self.dd_host_name,
            }

        metrics = []

        if 'finish_time' in job_stats.keys() and 'start_time' in job_stats.keys():
            elapsed_time = job_stats['finish_time'] - job_stats['start_time']
            metrics.append(collect('elapsed_time', elapsed_time.seconds))

        for key in self.to_collect:
            metrics.append(collect(key, job_stats.get(key, DEFAULT_MISSING)))

        logger.info('collected metrics, publishing to datadog')
        self.commit(metrics)

        # notify success/failure using DD checks
        self.publish_status(spider.name, job_stats.get('finish_reason'), tags)
