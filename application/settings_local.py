# -*- coding:utf-8 -*-

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'TBTEST',
        'USER': 'tbtest',
        'PASSWORD': 'test',
        'HOST': '192.168.1.90',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'OPTIONS': {
           "init_command": "SET default_storage_engine=MYISAM",
        }
    }
}
