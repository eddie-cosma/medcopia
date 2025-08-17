=========
Archive notice
=========

Thank you to everyone who followed Medcopia. Due to a combination of factors, I have chosen to archive this project. Interest in email alerts has waned, and there is no longer an easy way to send emails for free now that Sendgrid has eliminated their free tier. Additionally, the ASHP website recently implemented Cloudflare protection, making it harder to get drug shortage data programmatically. I am working on new ways to get this data and to incorporate it into `SageRx <https://github.com/coderxio/sagerx>`_.

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

You can download Medcopia by cloning the Github respository::

    git clone https://github.com/eddie-cosma/medcopia.git

=========
Configure
=========

The default configuration is stored as a dict in the ``medcopia/config/__init__.py`` file. Configuration should be customized further by setting environment variables to override the default values.


.. warning::
    Make sure to replace the ``SECRET_KEY`` with a generated value. In python, this can be done, for example, using::

        import secrets
        secrets.token_urlsafe(16)

Example configuration::

    SECRET_KEY=prod
    SERVER_NAME=localhost:5000
    PREFERRED_URL_SCHEME=https
    SQLALCHEMY_TRACK_MODIFICATIONS=False
    MAIL_DEFAULT_SENDER=alert@example.com
    MAIL_ALERT_TEMPLATE=d-sendgrid_alert_template_id
    MAIL_CONFIRM_TEMPLATE=d-sendgrid_confirm_template_id
    MAIL_DEFAULT_ASM_GROUP=12345
    RECAPTCHA_SITE_KEY=your_recaptcha_site_key
    RECAPTCHA_SECRET_KEY=your_recaptcha_secret_key
    SENDGRID_API_KEY=your_sendgrid_api_key


Testing configuration
---------

When testing, set the environment variable ``TESTING=True``. This prevents emails from being sent, and allows reCAPTCHA to be bypassed.

=========
Install with Docker (recommended)
=========

#. Create a .env file in the project root that contains the environment variables used to configure the application.
#. Create a uwsgi user (e.g., ``sudo useradd -M -s /sbin/false -U uwsgi``)
#. Take note of the UID and GID of the user you just created. You can find them using the ``id`` command::

    id -u uwsgi  # UID
    id -g uwsgi  # GID

#. Add the UID and GID to your .env file::

    UID=(the uwsgi UID)
    GID=(the uwsgi GID)
#. Create an ``instance`` directory in the project root and ensure it is owned by uwsgi (``sudo chown -R uwsgi:uwsgi instance``)
#. Run ``docker compose up``

=========
Install manually
=========

We recommend setting up a virtual environment before downloading the required dependencies using ``pip``::

    cd medcopia
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

We also recommend installing ``uwsgi`` as a WSGI service and ``nginx`` as a reverse proxy to run the web portion of Medcopia::

    pip install uwsgi
    sudo apt install nginx

Medcopia is composed of two components that require installation:

#. A Flask web service called ``signup`` that displays the website and allows users to subscribe to email alerts.
#. A module, ``scraper``, that scrapes the ASHP shortages list and checks for any changes whenever run. This should be run once a day.

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


.. warning::
    Do **not** use the existing uwsgi.ini file. It is meant for Docker-based deployments only.::

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

``scraper``
----------

``scraper`` is run as a module from the medcopia root directory::

    set -a
    source /path/to/.env
    set +a

    export PYTHONPATH=/path/to/medcopia
    python3 -m scraper

This script should be run once a day. The easiest way to do this automatically is by using ``cron``. For example, place the previous commands in a ``scraper.sh`` file in the ``medcopia/instance`` folder. Edit the crontab file using ``crontab -e`` and add the following to automatically run the script every day at 16:30::

    30 16 * * * /path/to/medcopia/instance/scraper.sh >> /path/to/medcopia/instance/scraper.log 2>&1


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
