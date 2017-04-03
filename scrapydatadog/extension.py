# -*- coding: utf-8 -*-
# vim:fenc=utf-8

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
    - log_count/DEBUG': 29,
    - log_count/INFO': 31,
    - log_count/WARNING': 13,
    - request_depth_max': 12,
    - response_received_count': 18,
    - scheduler/dequeued': 18,
    - scheduler/dequeued/memory': 18,
    - scheduler/enqueued': 18,
    - scheduler/enqueued/memory': 18,
    - start_time': datetime.datetime(2017, 4, 3, 9, 12, 20, 281530)}

"""

import logging
import os

from scrapy.exceptions import NotConfigured
from scrapy import signals

import datadog

logger = logging.getLogger(__name__)
# TODO make it accessible outside the extension
STATS_TO_COLLECT = ['item_scraped_count',
                    'response_received_count']
DEFAULT_MISSING = 0


class DatadogExtension(object):

    def __init__(self, sh_api_key, dd_api_key, dd_app_key, dd_host_name,
                 dd_metric_prefix, stats):
        self.sh_api_key = sh_api_key
        self.dd_api_key = dd_api_key
        self.dd_app_key = dd_app_key
        self.dd_host_name = dd_host_name
        self.dd_metric_prefix = dd_metric_prefix

        # make stats available within the spider
        # so one can collect custom metrics
        #
        #       >>> self.stats.inc_value('login_failed')
        #
        # learn more: https://doc.scrapy.org/en/latest/topics/stats.html
        self.stats = stats

    @classmethod
    def from_crawler(cls, crawler):
        sh_api_key = crawler.settings.get('SH_API_KEY')
        dd_api_key = crawler.settings.get('DATADOG_API_KEY')
        dd_app_key = crawler.settings.get('DATADOG_APP_KEY')
        dd_host_name = crawler.settings.get('DATADOG_SH_HOSTNAME')
        dd_metric_prefix = crawler.settings.get('DATADOG_METRIC_PREFIX')

        # try to read stats tags
        project_id = os.environ.get('SCRAPY_PROJECT_ID')
        spider_id = os.environ.get('SCRAPY_SPIDER_ID')

        if project_id is None or spider_id is None:
            logger.warning('no project/spider id provided, unable to tag stats')
            raise NotConfigured

        if not sh_api_key or not dd_api_key or not dd_app_key:
            logger.warning('no scrapinghub or datadog credentials found')
            raise NotConfigured

        ext = cls(sh_api_key, dd_api_key, dd_app_key, dd_host_name,
                  dd_metric_prefix, crawler.stats)

        crawler.signals.connect(ext.spider_closed,
                                signal=signals.spider_closed)

        return ext

    def tags(self, spider):
        # initialization made sure they were here
        project_id = os.environ.get('SCRAPY_PROJECT_ID')
        spider_id = os.environ.get('SCRAPY_SPIDER_ID')

        # TODO compute another tag based on spider arguments
        # (use case : some spiders split the work to avoid ban)
        return ['project:{}'.format(project_id),
                'spider_name:{}'.format(spider.name),
                'spider_id:{}'.format(spider_id)]

    def spider_closed(self, spider):
        # Fetch scrapy stats
        job_stats = self.stats.get_stats(spider)
        logger.debug('ScrapyStats from crawler: {}'.format(job_stats))

        # Build metrics list of dict to send to Datadog API
        tags = self.tags(spider)
        # ping datadog that a spider is done
        metrics = [{'metric': '{}.{}'.format(self.dd_metric_prefix, 'done'),
                    'points': 1,
                    'tags': tags}]

        if 'finish_time' in job_stats.keys() and 'start_time' in job_stats.keys():
            elapsed_time = job_stats['finish_time'] - job_stats['start_time']
            metrics.append({'metric': '{}.{}'.format(self.dd_metric_prefix, 'elapsed_time'),
                            'points': elapsed_time.seconds,
                            'tags': tags})

        for key in STATS_TO_COLLECT:
            metrics.append({'metric': '{}.{}'.format(self.dd_metric_prefix, key),
                            'points': job_stats.get(key, DEFAULT_MISSING),
                            'tags': tags})

        # initialize API client
        logger.debug('Configure API client with credentials')
        options = {'api_key': self.dd_api_key,
                   'app_key': self.dd_app_key,
                   'host_name': self.dd_host_name}
        datadog.initialize(**options)
        logger.info('Client initialized, will now send metrics: {}'.format(metrics))

        res = datadog.api.Metric.send(metrics)
        logger.debug('API call result: {}'.format(res))
