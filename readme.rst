.. image:: signup/static/logo.png
    :alt: Medcopia Logo
    :align: center

=========
Medcopia
=========

Medcopia is a hosted subscription service that tracks changes to the `ASHP drug shortages list <https://www.ashp.org/drug-shortages/current-shortages>`_ and sends email alerts to subscribers whenever changes are detected.

=========
Download
=========

Medcopia is currently installable by cloning the Github respository::

    git clone https://github.com/eddie-cosma/medcopia.git

We recommend setting up a virtual environment before downloading the required dependencies using ``pip``::

    cd medcopia
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

We also recommend installing ``uwsgi`` as a WSGI service and ``nginx`` as a reverse proxy to run the web portion of Medcopia::

    pip install uwsgi
    sudo apt install nginx

=========
Configure
=========

The default configuration is stored as a dict in the ``medcopia/config/__init__.py`` file. Configuration should be customized further by creating a ``medcopia/instance/config.json`` file to override the default values.


.. warning::
    Make sure to replace the ``SECRET_KEY`` with a generated value. In python, this can be done, for example, using::

        import secrets
        secrets.token_urlsafe(16)

Example configuration::

    {
      "SECRET_KEY": "prod",
      "SERVER_NAME": "localhost:5000",
      "PREFERRED_URL_SCHEME": "https",
      "SQLALCHEMY_TRACK_MODIFICATIONS": false,
      "MAIL_SERVER": "mail.example.org",
      "MAIL_PORT": 465,
      "MAIL_USERNAME": "medcopia@example.org",
      "MAIL_PASSWORD": "password",
      "MAIL_DEFAULT_SENDER": "Medcopia Shortage Alerts <medcopia@example.org>",
      "MAIL_PER_DAY_MAX": 5,
      "RECAPTCHA_SITE_KEY": "your_recaptcha_site_key",
      "RECAPTCHA_SECRET_KEY": "your_recaptcha_secret_key",
      "REDDIT_KEY": "your_reddit_api_key",
      "REDDIT_SECRET": "your_reddit_api_secret",
      "REDDIT_USER_AGENT": "your_praw_user_agent",
      "REDDIT_USERNAME": "your_reddit_username",
      "REDDIT_PASSWORD": "your_reddit_password",
      "REDDIT_SUBREDDIT": "drugshortages",
      "REDDIT_NEW_SHORTAGE_FLAIR_ID": "362c42a2-474c-11ec-bbd5-0ed2a92f10f6"
    }

Note that currently only implicit TLS SMTP connections are supported. STARTTLS and unencrypted SMTP are not supported.

``MAIL_PER_DAY_MAX`` refers to the number of signup attempts that are allowed per email address per day. This value is reset by ``reset_email_counter.py`` daily (see Install section below).

Testing configuration
---------

A testing configuration can be used by creating ``medcopia/instance/test_config.json`` in the same format as the example above. When testing, set the environmental variable ``TESTING=True`` to use the testing configuration, to prevent emails from being sent, and to bypass reCAPTCHA.

=========
Install
=========

Medcopia is composed of three components that require installation:

#. A Flask web service called ``signup`` that displays the website and allows users to subscribe to email alerts.
#. A module, ``scraper``, that scrapes the ASHP shortages list and checks for any changes whenever run. Changes are sent to users via email and submitted to the configured subreddit. This should be run once a day.
#. A script called ``reset_email_counter.py`` that resets the number of registration attempts for each individual email address in the database. Registration attempts are limited by the ``MAIL_PER_DAY_MAX`` configuration value to prevent abuse. This script should be run once a day.

``signup`` web service
---------

The web service should be configured to run on a WSGI. For example, if using ``uwsgi``, you can save a ``config.ini`` file to the medcopia root directory::

    [uwsgi]
    module = signup

    master = true
    processes = 5

    socket = /tmp/signup.sock
    chmod-socket = 666
    vacuum = true

    die-on-term = true

This configuration can then be run::

    uwsgi --ini config.ini

Once the WSGI service is running, a reverse proxy like ``nginx`` can be configured to point to the WSGI socket, allowing web access::

    # /etc/nginx/sites-available/default
    server {
        listen 80 default_server;
        listen [::]:80 default_server;

        listen 443 ssl default_server;
        listen [::]:443 ssl default_server;

        # Substitute your own SSL certificates
        ssl_certificate /etc/ssl/certs/your_ssl_certificate.pem;
        ssl_certificate_key /etc/ssl/private/your_ssl_certificate_key.pem;

        location / { try_files $uri @signup; }
        location @signup {
            include uwsgi_params;
            uwsgi_param HTTP_HOST $server_name;
            uwsgi_pass unix:/tmp/signup.sock;
        }

        # Substitute your own server name
        server_name example.com;
    }

Restart ``nginx`` after saving your configuration::

    sudo systemctl restart nginx

You can use ``systemd`` to run this config automatically on system start. DigitalOcean has a `fantastic tutorial <https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-uswgi-and-nginx-on-ubuntu-18-04>`_ giving more detail on this setup.

``scraper`` and ``reset_email_counter``
----------

``scraper`` is run as a module from the medcopia root directory::

    export PYTHONPATH=/path/to/medcopia
    python3 -m scraper

``reset_email_counter`` is run as a script from the ``helpers`` directory::

    export PYTHONPATH=/path/to/medcopia
    python3 helpers/reset_email_counter.py

These scripts should be run once a day. The easiest way to do this automatically is by using ``cron``. For example, place the previous two commands in a ``reset_email_counter.sh`` file in the ``medcopia/instance`` folder. Edit the crontab file using ``crontab -e`` and add the following to automatically run the script every day at 03:00::

    0 3 * * * /path/to/medcopia/instance/reset_email_counter.sh >> /path/to/medcopia/instance/reset_email_counter.log 2>&1

The same can be done for the ``scraper`` module.

=========
Contributing
=========

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

=========
License
=========

This software is licensed under the `GPL 3.0 <https://github.com/eddie-cosma/medcopia/blob/master/LICENSE>`_ license.

=========
Disclaimer
=========

This service is not affiliated, associated, authorized, or endorsed by the American Society of Health-System Pharmacists or the University of Utah Drug Information Service. All names and brands are properties of their respective owners.