import logging
import os

from scrapinghub import HubstorageClient
from scrapy.exceptions import NotConfigured
from scrapy import signals

from datadog import initialize, api

logger = logging.getLogger(__name__)


class DatadogExtension(object):

    def __init__(self, sh_api_key, dd_api_key, dd_app_key, dd_host_name,
                 dd_metric_prefix):
        self.sh_api_key = sh_api_key
        self.dd_api_key = dd_api_key
        self.dd_app_key = dd_app_key
        self.dd_host_name = dd_host_name
        self.dd_metric_prefix = dd_metric_prefix

    @classmethod
    def from_crawler(cls, crawler):
        sh_api_key = crawler.settings.get('SH_API_KEY')
        dd_api_key = crawler.settings.get('DATADOG_API_KEY')
        dd_app_key = crawler.settings.get('DATADOG_APP_KEY')
        dd_host_name = crawler.settings.get('DATADOG_SH_HOSTNAME')
        dd_metric_prefix = crawler.settings.get('DATADOG_METRIC_PREFIX')

        if not sh_api_key or not dd_api_key or not dd_app_key:
            raise NotConfigured

        ext = cls(sh_api_key, dd_api_key, dd_app_key, dd_host_name,
                  dd_metric_prefix)
        crawler.signals.connect(ext.spider_closed,
                                signal=signals.spider_closed)
        return ext

    def spider_closed(self, spider):
        project_id = os.environ.get('SCRAPY_PROJECT_ID')
        spider_id = os.environ.get('SCRAPY_SPIDER_ID')
        job_id = os.environ.get('SCRAPY_JOB_ID')

        if job_id is not None:
            # Fetch scrapy stats
            hc = HubstorageClient(auth=self.sh_api_key)
            job = hc.get_job("{}/{}/{}".format(project_id, spider_id, job_id))
            job_stats = job.metadata

            # Build metrics list of dict to send to Datadog API
            tags=["project:{}".format(project_id),
                  "spider:{}".format(spider_id)]
            stats_to_collect = ["item_scraped_count",
                                "response_received_count"]
            metrics = [{'metric': "{}.{}".format(self.dd_metric_prefix, 'done'),
                        'points': 1,
                        'tags': tags}]
            if 'finish_time' in job_stats.keys() and 'start_time' in job_stats.keys():
                elapsed_time = job_stats['finish_time'] - job_stats['start_time']
                metrics.append({'metric': "{}.{}".format(self.dd_metric_prefix, 'elapsed_time'),
                                'points': elapsed_time.seconds,
                                'tags': tags})

            logger.info('[DATADOG] Configure API client with credentials: DATADOG_API_KEY={} DATADOG_APP_KEY={}'.format(self.dd_api_key, self.dd_app_key))
            for k, v in job_stats.iteritems():
                if k in stats_to_collect:
                    metrics.append({'metric': "{}.{}".format(self.dd_metric_prefix, k),
                                    'points': v,
                                    'tags': tags})

            # initialize API client
            options = {
                'api_key': self.dd_api_key,
                'app_key': self.dd_app_key,
                'host_name': self.dd_host_name
            }
            initialize(**options)
            logger.debug('[DATADOG] Client initialized, will now send metrics: {}'.format(metrics))

            # Send metrics and print API response
            res = api.Metric.send(metrics)
            logger.info('[DATADOG] API call result: {}'.format(res))
