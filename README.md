# Scrapy Datadog Extension



Branch | CI                                                                                                                                 | Python Versions
-------|------------------------------------------------------------------------------------------------------------------------------------|---------------
master |[![CircleCI](https://circleci.com/gh/Kpler/scrapy-datadog-extension.svg?style=svg)](https://circleci.com/gh/Kpler/scrapy-datadog-extension)|![pythonVersion](https://img.shields.io/badge/python-3.6-blue.svg) ![pythonVersion2](https://img.shields.io/badge/python-2.7-blue.svg?longCache=true&style=flat)


**scrapy-datadog-extension** is a [Scrapy extension](scrapy-ext) to send metrics from your spiders
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


## Useful links

- [Datadog API](http://docs.datadoghq.com/api/)
- [ScrapingHub extensions](https://doc.scrapinghub.com/addons.html)

---

### By the way we're hiring [across the world](https://careers.kpler.com/) 👇

<img src="https://s3-eu-west-1.amazonaws.com/www.kpler.com/assets/images/footer/kpler-offices.png" alt="Kpler Offices" />

Join our engineering team to help us building data intensive projects!
We are looking for people who love their craft and are the best at it.

- Data Engineers in [Singapore](https://careers.kpler.com/jobs/data-engineer_singapore) and [Paris](https://careers.kpler.com/jobs/data-python-developer_paris_KPLER_yV1k4qO)
- Data Support Engineers in [Singapore](https://careers.kpler.com/jobs/software-production-engineer-singapore_singapore)
- Data Engineer interns in [Singapore](https://careers.kpler.com/jobs/data-engineer-singapore_singapore) and [Paris](https://careers.kpler.com/jobs/data-python-developer-internship_paris)

<p align="center">
  <br>
  <img src="https://s3-eu-west-1.amazonaws.com/www.kpler.com/assets/images/logo/kpler_logo_orange_mail_signature.png" alt="Kpler logo" />
  <br>
  <br>
</p>


<p align="center"><i>This code is <a href="https://github.com/Kpler/scrapy-datadog-extension/blob/master/LICENSE.md">MIT licensed</a>.
<br/>Designed & built by Kpler engineers with a </i>💻<i> and some </i>🍣.


[dd]: https://www.datadoghq.com/
[scrapy-ext]: https://doc.scrapy.org/en/latest/topics/extensions.html
[stats]: https://doc.scrapy.org/en/latest/topics/stats.html
[logo]: https://s3-eu-west-1.amazonaws.com/www.kpler.com/assets/images/logo/kpler_logo_orange_mail_signature.png
