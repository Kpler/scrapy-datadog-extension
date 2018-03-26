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

## Extension built-in tags

    - spider_name
    - project_id

"""

import logging

import datadog
from datadog.api.constants import CheckStatus
from scrapy import signals

from scrapydatadog import utils
# prevent Scrapy `settings` overwrite
from scrapydatadog import settings as ext_settings

logger = logging.getLogger(__name__)


class DatadogExtension(object):

    def __init__(self, settings, stats):
        # properly identify the job
        self.project_id = settings['SCRAPY_PROJECT_ID']

        self.dd_api_key = settings['DATADOG_API_KEY']
        self.dd_app_key = settings['DATADOG_APP_KEY']
        self.dd_host_name = settings.get('DATADOG_HOST_NAME', ext_settings.DEFAULT_DD_HOST_NAME)
        self.dd_metric_prefix = settings.get('DATADOG_METRICS_PREFIX',
                                             ext_settings.DEFAULT_DD_PREFIX)
        self.dd_service_check = settings.get('DATADOG_SERVICE_CHECK',
                                             ext_settings.DEFAULT_SERVICE_CHECK)

        # extend default behaviors
        self.to_collect = utils.make_list(settings.get('DATADOG_CUSTOM_METRICS',
                                          ext_settings.DEFAULT_CUSTOM_METRICS))
        self.custom_tags = utils.make_list(settings.get('DATADOG_CUSTOM_TAGS', []))

        # allow the rest of the extension to access stats logic/data
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        ext_settings.merge_env(crawler.settings)
        ext_settings.validate_conf(crawler.settings)

        ext = cls(crawler.settings, crawler.stats)

        crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        return ext

    def build_tags(self, spider):
        """Aggregate and format spider tags.

        The extension merges tags from 3 different places:

            - built-in: always good to segment by project and spider
            - settings: a common place for generic, static or poecjt wide tags
            - `spider.tags` to let spiders dynamically set them after init

        """
        dynamic_tags = getattr(spider, 'tags', [])

        return ['project:{}'.format(self.project_id),
                'spider_name:{}'.format(spider.name),
                ] + self.custom_tags + dynamic_tags

    def _metrics_fmt(self, key):
        sane_key = utils.sanitize_metric_name(key)
        return '{}.{}'.format(self.dd_metric_prefix, sane_key)

    def commit(self, metrics):
        res = datadog.api.Metric.send(metrics)
        logger.debug('API call result: {}'.format(res))

    def publish_status(self, spider_name, finish_reason, tags):
        status = ext_settings.DD_STATUS_MAPPING.get(finish_reason, CheckStatus.UNKNOWN)
        msg = 'Spider {} ended because: {}'.format(spider_name, finish_reason)

        logger.info(msg)
        datadog.api.ServiceCheck.check(check=self.dd_service_check,
                                       status=status,
                                       message=msg,
                                       host=ext_settings.DEFAULT_DD_HOST_NAME,
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
        tags = self.build_tags(spider)

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

        # TODO allow regex matching
        for key in self.to_collect:
            metrics.append(collect(key, job_stats.get(key, ext_settings.DEFAULT_MISSING)))

        logger.info('collected metrics, publishing to datadog')
        self.commit(metrics)

        # notify success/failure using DD checks
        self.publish_status(spider.name, job_stats.get('finish_reason'), tags)
