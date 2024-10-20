from pathlib import Path
import os
import pyrebase
import firebase_admin
from firebase_admin import credentials, db
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-5q9@&9d@m&$huwgtoe3g*a%m-c&#+du)u=f&+1^vtq0p&s(5z('

DEBUG = True

ALLOWED_HOSTS = ['*']


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Gou.urls'

 

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Gou.wsgi.application'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465  
EMAIL_USE_SSL = True  
EMAIL_USE_TLS = False  
EMAIL_HOST_USER = 'gou2udec@gmail.com' 
EMAIL_HOST_PASSWORD = 'fnmz tdas oydh wjvs'  




# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases



SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'NAME': 'GoUV2',  
        'CLIENT': {
            'host': 'mongodb+srv://gouudec2024:gou22024@gouv2.fbdwx.mongodb.net/?retryWrites=true&w=majority&appName=GoUv2',
        }
    }
}





LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'accounts/static')]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



