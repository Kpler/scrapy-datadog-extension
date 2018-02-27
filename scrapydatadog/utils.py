# -*- coding: utf-8 -*-


def sanitize_metric_name(key):
    """Ensure metrics are statsd/datadog compliant, ie use lower case and
    dot-seperated namespace.

    Examples:
        >>> # change nothing on good format
        >>> sanitize_metric_name('some.metrics.name')
        'some.metrics.name'
        >>> # otherwise:
        >>> sanitize_metric_name('SOME.weird.name')
        'some.weird.name'
        >>> sanitize_metric_name('some/weird/name')
        'some.weird.name'

    """
    return key.lower().replace('/', '.')


def make_list(value, sep=','):
    """Split strings around `sep` or return as is.

    Examples:
        >>> make_list('foo,bar')
        ['foo', 'bar']
        >>> make_list('foo,bar', sep='.')
        ['foo,bar']
        >>> make_list(3)
        3

    """
    return value.split(sep) if isinstance(value, str) else value
