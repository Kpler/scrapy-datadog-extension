# Scrapy Datadog Extension

[![CircleCI](https://circleci.com/gh/Kpler/scrapy-datadog-extension.svg?style=svg)](https://circleci.com/gh/Kpler/scrapy-datadog-extension)

scrapy-datadog-extension is a [Scrapy extension](scrapy-ext) to send metrics from your spiders
executions to [Datadog][dd] ([scrapy stats][stats]).

## Installation

There is no public pre-packaged version yet. If you want to use it you
will have to clone the project and make it installable easilly from the
`requirements.txt`.


## Configuration

First, you will need to include the extension to the `EXTENSIONS` dict located
in your `settings.py` file. For example:

    EXTENSIONS = {
        'scrapy-datadog-extension': 1,
    }

Then you need to provide the followings variables, directly from the scrapinghub
settings of your jobs:

- `DATADOG_API_KEY`: Your Datadog API key.
- `DATADOG_APP_KEY`: Your Datadog APP key.
- `DATADOG_CUSTOM_TAGS`: List of tags to bind on metrics
- `DATADOG_CUSTOM_METRICS`: Sub list of metrics to send to Datadog
- `DATADOG_METRICS_PREFIX`: What prefix you want to apply to all of your metrics,
  _e.g._: `kp.`
- `DATADOG_HOST_NAME`: The hostname you want your metrics to be associated
  with. _e.g._: `app.scrapinghub.com`.


Sometimes one might need to set tags at runtime. For example to compute
them out of the spider arguments. To allow such scenario, just set a
`tags` attribute to your spider with a list of `statsd` compatible keys
(i.e. `["foo", ...]` or `["foo:bar", ...]`). Note that all metrics will
then be tagged as well.


## How it works

Basically, this extension will, on the `spider_closed` signal execution, collect
the scrapy stats associated to a given _projct/spider/job_ and extract a list
of variables listed in a `stats_to_collect` list, custom variables will be also
be added:

- `elapsed_time`: which is a simple computation of `finish-time - start_time`.
- `done`: a simple counter, acting like a ping to indicate that a job is ran
  regularly.

At the end, we have a list of metrics, with tags associated (to enable better
filtering from Datadog):

- `project`: The scrapinghub project ID.
- `spider_name`: The scrapinghub spider name as defined in the spider
  class.

Then, everything is sent to Datadog, using the Datadog API.


## Known issues

- Sometimes, when the `spider_closed` is executed right after the job
  completion, some scrapy stats are missing so we send incomplete list
  of metrics, preventing us to rely 100% on this extension.


## TODO

- [ ] Include the name of the project/spider/job instead of simply send its ID.
- [x] Make the `stats_to_collect` configurable from the ScrapingHub spiders
  settings console.
- [ ] Find a way to ensure that all the scrapy stats are collected prior to
  send them.


## Useful links

- [Datadog API](http://docs.datadoghq.com/api/)
- [ScrapingHub extensions](https://doc.scrapinghub.com/addons.html)



[dd]: https://www.datadoghq.com/
[scrapy-ext]: https://doc.scrapy.org/en/latest/topics/extensions.html
[stats]: https://doc.scrapy.org/en/latest/topics/stats.html
