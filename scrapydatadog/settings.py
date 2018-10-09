# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
import logging
import os

from scrapy.exceptions import NotConfigured
from datadog.api.constants import CheckStatus
import six

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


def getbool(conf, key):
    """Emulation of scrapy.Settings;getbool.

    It allows the config to remain agnostic from Scrapy specificities. Not that
    it brings much to the table but that's really cheap to make it so.

    Examples:
        >>> getbool({}, 'foo')
        False
        >>> getbool({'foo': 'no'}, 'foo')
        False
        >>> getbool({'foo': 'yes'}, 'foo')
        True
        >>> getbool({'foo': 'True'}, 'foo')
        True

    """
    return conf.get(key) in [True, 'True', 'true', 'yes', 'y']


def validate_conf(conf):
    """Abort extension setup if we don't have all the required settings."""
    # shortcut to disable the extension - especially useful for local
    # development that doesn't require metrics
    # if conf.get()
    if getbool(conf, 'DATADOG_DISABLED'):
        logger.warning('extension explicitely disabled')
        raise NotConfigured

    for key in MANDATORY_SETTINGS:
        if key not in conf:
            logger.warning('datadog extension mandatory setting missing: {}'.format(key))
            logger.warning('scraper will go on but extension will be disabled.')
            raise NotConfigured
        elif conf[key] is None:
            logger.warning('setting {} was set to `None`.'.format(key))
            raise NotConfigured


def merge_env(settings):
    """Merge settings setup from env and/or scrapy settings.

    Note that Scrapy `settings` take precedence over env and won't be modified
    if already set.

    Also, this method doesn't return anything. Instead it mutates the
    given dict on purpose.

    """
    ALL_SETTINGS = MANDATORY_SETTINGS + CUSTOM_SETTINGS

    settings.update({
        k: v for k, v in six.iteritems(os.environ)
        if k in ALL_SETTINGS and k not in settings
    })
