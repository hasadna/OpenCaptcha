# OpenCaptcha

[![Build Status](https://img.shields.io/travis/hasadna/OpenCaptcha/master.svg)](https://travis-ci.org/hasadna/OpenCaptcha)
[![Coveralls](http://img.shields.io/coveralls/hasadna/OpenCaptcha.svg?branch=master)](https://coveralls.io/r/hasadna/OpenCaptcha?branch=master)

OpenCaptcha is a completely self hosted CAPTCHA library that allows web app 
developers to generate challenges based on data specific to their site.
The information from those challenges is presented graphically to the user 
(as an image - typically a chart), who then needs to choose the correct answer 
out of a closed set of options, based on the information in the image.

For example, a site sharing information about the coronavirus outbreak may
generate a bar chart showing the 3 countries with the most active 
cases for that day and ask the user to respond with the country that had the 
most cases. The types of challenges available are templates that can be 
configured by the hosting site as described below.

## Installation
Run `pip install open-captcha`

## Using OpenCaptcha on your site
To use OpenCaptcha, the site's backend needs to provide the following:
- **Data tables** the templates can use to generate challenges. The data would 
usually be SELECTed from the site's DB.
- A **configuration** for a set of pre-built challenge templates. This would 
usually come in the form of a static JSON config file. Each configuration item
tells open-captcha which template to use and provides the configuration for it
to generate unique challenges from the data. 

When a challenge is generated (see flow below), it consists of three parts:
- A `Challenge` structure comprising the information shown to the user. Specifically:
    - The question (string).
    - A chart (PNG image) shown to the user.
    - A list of possible answers (strings).
- A `ServerContext` structure, which should be stored on the server and is used
to verify the user's answer.
- A `ChallengeID`, which is an opaque token used to connect the `Challenge` to
 its `ServerContext`. 

The suggested backend flow would be:
1. At startup, construct a `CaptchaGenerator` object, providing it with data 
tables and the configuration for the templates you want to use.
1. Call `generator.generate_challenge()`, which randomly selects one of the templates
and uses it to generate a triplet of `ChallengeId`, `Challenge` and `ServerContext`.
1. The server should store the `ServerContext` on some cache service (e.g. redis),
keyed by the `ChallengeId`. The context should be stored with a short TTL (but long
enough to allow legitimate users to answer the question).
1. The `Challenge` and `ChallengeId` are then sent to the client, which presents
them to the user. Once the user answers, the user's answer is sent together with 
the `ChallengeId` back to the server for verification.
1. The server retrieves the `ServerContext` from cache using the `ChallengeId`.
If the context is not found (wrong token or TTL expired) this counts as a verification
failure.
1. The server calls `generator.verify_response()`, passing the user's answer
and the `ServerContext`. The method returns True iff the answer is correct and
was received within a specified timeout. A configurable number of typos in the 
answer is allowed. 

An example flow can be found in [test_integration.py](https://github.com/hasadna/OpenCaptcha/blob/master/tests/test_integration.py),
which shows the above steps in the form of a unit test. These do not include the calling server's
logic: how the configuration is loaded, how the data is retrieved from the DB, how the cache and 
communication with the client is managed. These are left out on purpose in order to allow the
server developer the maximum amount of flexibility in implementing those aspects.

## Extending the library by adding new challenge templates
OpenCaptcha comes with a small number of pre-defined templates. These can be 
extended over time by the developers working on OpenCaptcha itself, but they
can also be extended by server developers using OpenCaptcha to add unique types
of challenges that make sense for their site.

To add a new type of challenge, simply create a subclass of `ChallengeTemplate`
and implement the following interface:
1. The class attribute `config_name` should be the name of the template, which is
how it's referred to from the configuration.
1. The class's `__init__()` method is free to accept any type and number of parameters. 
These are specified in the configuration item that references that template. Typical 
parameters would be the question text, which data tables and columns to get the 
data from and other template-specific parameters.
1. Implement the `generate_challenge()` method. This method receives the data and
should return a `Challenge` object and the correct answer.

See the [code](https://github.com/hasadna/OpenCaptcha/tree/master/open_captcha) 
and [tests](https://github.com/hasadna/OpenCaptcha/tree/master/tests) for more details.
