"""
Django settings for StrongerAB1 project.

Generated by 'django-admin startproject' using Django 2.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '6pl(ljdspnr)!2_jk^--_%t8at2#9qg+gm3k$6q@j@1l(8o20+'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1','0.0.0.0','localhost']

# Application definition
LOGGING = {
    'version' : 1,
    'disable_existing_loggers' : False,
    'formatters' : {
        'detailed' : {
            'format' : '{levelname} {asctime} {module} {lineno} {process:d} {thread:d} {message}',
            'style' : '{',
        }

    },
    'handlers' : {
        'console' : {
            'class' : 'logging.StreamHandler',
            'formatter' : 'detailed',
            'level': 'DEBUG'
        },
        'file' : {
            'level' : 'DEBUG',
            'class' : 'logging.handlers.RotatingFileHandler',
            'filename' : 'logs/logfile',
            'formatter' : 'detailed',
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5
        }

    },
    'root' : {
        'handlers' : ['console','file'],
        'level' : 'DEBUG'
    },
    'loggers': {
        'django': {
            'handlers': ['console','file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'background_task': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'background_task',
    'Influencers',
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

ROOT_URLCONF = 'StrongerAB1.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'StrongerAB1.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
#  }
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'influ1',
        'USER': 'postgres',
        'PASSWORD': 'abc123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True
BACKGROUND_TASK_RUN_ASYNC = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static/')

STATICFILES_DIR = (
 	os.path.join(BASE_DIR,'Influencers/static'),
 )
paid_unpaid_choices = ['','Paid','Unpaid','OK']
order_status_choices = ['', 'SHIPPED','CONFIRMED', 'PARTIAL', 'SHIPPED', 'ARCHIVED', 'DELETED' ]
portals=[('',''), ('Linked In','Linked In'),('Indeed','Indeed'),('Glassdoor','Glassdoor'),('Other','Other')]
b2b_mandatory_fields = ["Company Name", "Full Name", "Designation", "Email", "Linkedin ID", "Position", "Job Location", "Job Posting Links", "Company Website", "Company Linkedin" ]
LOGIN_URL='/login'
LOGIN_REDIRECT_URL='/all_influencers'
LOGOUT_REDIRECT_URL='/all_influencers'
LEADSPAN=30
ADMINSPAN=100
adminMsg=" if you are not admin"

influencer_post_status = ['','Published', 'Reminder1', 'Reminder2', 'Abandoned']
#influencer_mandatory_fields =['Instagram Username','Country','Influencer/Prospect','ID']
influencer_mandatory_fields =['Country','Influencer/Prospect','ID']
is_influencer_choices = ["", "Prospect", "Influencer"]
is_answered_choices = ["","Yes", "No"]
centra_key = "2de0107b9b16e994f1894e514f031a21"
centra_api_url = "https://stronger.centra.com/graphql"
centra_api_start_date = "2020-12-01"