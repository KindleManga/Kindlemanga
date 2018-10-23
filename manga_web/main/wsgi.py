"""
WSGI config for main project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "main.settings")
os.environ['DATABASE_NAME'] = 'kindlemanga'
os.environ['DATABASE_USER'] = 'tu'
os.environ['DATABASE_PASSWORD'] = 'Tu0703$$'
os.environ['MEDIAFIRE_EMAIL'] = 'tu0703@gmail.com'
os.environ['MEDIAFIRE_PASSWORD'] = '4R7G$b44T1kTYbSsLWT&'
os.environ['RECAPTCHA_PUBLIC_KEY'] = '6LfgUlMUAAAAADBtie83trHlWuYSO5b700QCriNk'
os.environ['RECAPTCHA_PRIVATE_KEY'] = '6LfgUlMUAAAAAGQpeev4AVlORR1Mo9xiLP2GkbRD'
os.environ['GMAIL_EMAIL'] = 'meatyminus@gmail.com'
os.environ['GMAIL_PASSWORD'] = '0okami$$'
os.environ['VENV_PATH'] = '/home/tu/Kindlemanga/venv/bin'

application = get_wsgi_application()
