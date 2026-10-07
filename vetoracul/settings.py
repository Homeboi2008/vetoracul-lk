from pathlib import Path
from Config import DjangoSettings, DatabaseSettings, EmailSettings
from django.contrib import messages

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = DjangoSettings.SECRET_KEY

DEBUG = not DjangoSettings.IS_PRODUCTION

ALLOWED_HOSTS = DjangoSettings.ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = DjangoSettings.CSRF_TRUSTED_ORIGINS

if not DjangoSettings.IS_PRODUCTION:
    STATICFILES_DIRS = DjangoSettings.STATICFILES_DIRS
else:
    STATIC_ROOT = DjangoSettings.STATIC_ROOT

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'vetoracul_app'
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

ROOT_URLCONF = 'vetoracul.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'vetoracul_app' / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',

                'vetoracul_app.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'vetoracul.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': DatabaseSettings.DATABASE_ENGINE,
        'NAME': DatabaseSettings.DATABASE_NAME,
        'USER': DatabaseSettings.DATABASE_USER,
        'PASSWORD': DatabaseSettings.DATABASE_PASSWORD,
        'PORT': DatabaseSettings.DATABASE_PORT,
        'HOST': DatabaseSettings.DATABASE_HOST
    }
}


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


LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'static/'

AUTH_USER_MODEL = 'vetoracul_app.User'

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

EMAIL_BACKEND =  EmailSettings.EMAIL_BACKEND
EMAIL_HOST = EmailSettings.EMAIL_HOST
EMAIL_PORT = EmailSettings.EMAIL_PORT
EMAIL_HOST_USER = EmailSettings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = EmailSettings.EMAIL_HOST_PASSWORD
EMAIL_USE_TLS = EmailSettings.EMAIL_USE_TLS
EMAIL_USE_SSL = EmailSettings.EMAIL_USE_SSL
DEFAULT_FROM_EMAIL = EmailSettings.DEFAULT_FROM_EMAIL

PASSWORD_RESET_TIMEOUT = 60 * 60 * 24 * 3

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

AUTHENTICATION_BACKENDS = [
    'vetoracul_app.backends.EmailOrUsernameBackend',
]

MESSAGE_TAGS = {
    messages.DEBUG: 'p-2 list-group-item list-group-item-secondary text-center',
    messages.INFO: 'p-2 list-group-item list-group-item-info text-center',
    messages.SUCCESS: 'p-2 list-group-item list-group-item-success text-center',
    messages.WARNING: 'p-2 list-group-item list-group-item-warning text-center',
    messages.ERROR: 'p-2 list-group-item list-group-item-danger text-center',
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'