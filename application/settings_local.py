# -*- coding:utf-8 -*-

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'TBTEST',
        'USER': 'TBTEST',
        'PASSWORD': 'tbtest',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
        'OPTIONS': {
           "init_command": "SET default_storage_engine=MYISAM",
        }
    }
}
