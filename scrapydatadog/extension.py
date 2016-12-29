import os

from scrapinghub import HubstorageClient
from scrapy.exceptions import NotConfigured

from datadog import initialize, api


class DatadogExtension(object):

    def __init__(self, sh_api_key, dd_api_key, dd_app_key):
        self.sh_api_key = sh_api_key
        self.dd_api_key = dd_api_key
        self.dd_api_key = dd_api_key

    @classmethod
    def from_crawler(cls, crawler):
        sh_api_key = crawler.settings.get('SH_API_KEY')
        dd_api_key = crawler.settings.get('DATADOG_API_KEY')
        dd_app_key = crawler.settings.get('DATADOG_APP_KEY')
        if not sh_api_key or not dd_api_key or not dd_app_key:
            raise NotConfigured
        ext = cls(sh_api_key, dd_api_key, dd_app_key)
        crawler.signals.connect(ext.spider_closed,
                                signal=signals.spider_closed)
        return ext

    def spider_closed(self, spider):
        project_id = os.environ.get('SCRAPY_PROJECT_ID')
        spider_id = os.environ.get('SCRAPY_SPIDER_ID')
        job_id = os.environ.get('SCRAPY_JOB_ID')

        if job_id is not None:
            # Fetch scrapystats for the given project_id/spider_id/job_id
            stats_to_collect = ["finish_reason",
                                "item_scraped_count",
                                "elapsed_time"]
            hc = HubstorageClient(auth=self.sh_api_key)
            job = hc.get_job("{}/{}/{}".format(project_id, spider_id, job_id))
            job_stats = job.metadata
            elapsed_time = job_stats['finish_time'] - job_stats['start_time']
            job_stats['elapsed_time'] = elapsed_time

            # Send scrapy stats to Datadog
            options = {
                'api_key': self.dd_api_key,
                'app_key': self.dd_app_key
            }
            initialize(**options)
            for k, v in job_stats.iteritems():
                if k in stats_to_collect:
                    api.Metric.send(metric="kp.sh.spiders.stats.{}".format(k),
                                    points=v,
                                    tags=["project:{}".format(project_id),
                                          "spider:{}".format(spider_id),
                                          "job:{}".format(job_id)])
