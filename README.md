# scrapy-datadog-extension

scrapy-datadog-extension is an extension to  send metrics from your spiders
executions to Datadog (scrapy stats).

## Installation

There is no public version of this package yet, if you want to use it you will
have to clone the project and make it installable easilly from the `scrapinghub-requirements.txt`.

## Configuration

First, you will need to include the extension to the `EXTENSIONS` dict located
in your `settings.py` file. For example:

    EXTENSION = {
        'scrapy-datadog-extension': 1,
    }

Then you need to provide the followings variables, directly from the scrapinghub
settings of your jobs:

- `DATADOG_API_KEY`: Your Datadog API key.
- `DATADOG_APP_KEY`: Your Datadog APP key.
- `DATADOG_METRIC_PREFIX`: What prefix you want to apply to all of your metrics,
  _e.g._: `kp.`
- `DATADOG_SH_HOSTNAME`: The hostname you want your metrics to be associated
  with. _e.g._: `app.scrapinghub.com`.

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
- `spider`: The scrapinghub spider ID.

Then, everything is sent to Datadog, using the Datadog API.

For now, we still have some issues: Sometimes, when the spider_closed is
executed right after the job completion, some scrapy stats are missing so we
send incomplete list of metrics, preventing us to rely 100% on this extension.
Maybe a _retry_ solution ( try to fetch stats every 1,2,3,5,8,13,21 seconds for
example) might be a good solution?


## Useful links

- Datadog API: http://docs.datadoghq.com/api/
- ScrapingHub Hubstorage: https://pypi.python.org/pypi/hubstorage
- ScrapingHub extensions: https://doc.scrapinghub.com/addons.html
- Get access to the spider Job and Project IDs: https://github.com/Kpler/scrapy-job-parameters-extension

## TODO
- [ ] Also the name of the project/spider/job instead of simply send its ID.
- [ ] Make the `stats_to_collect` configurable from the ScrapingHub spiders
  settings console.
- [ ] Find a way to ensure that all the scrapy stats are collected before to
  send them.
