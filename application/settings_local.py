# -*- coding:utf-8 -*-
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'TBTEST',
        'USER': 'TBTEST',
        'PASSWORD': 'tbtest',
        'HOST': '192.168.1.32',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'OPTIONS': {
           "init_command": "SET default_storage_engine=MYISAM",
        }
    }
}



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}
