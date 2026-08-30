from pathlib import Path
from Config import DjangoSettings, DatabaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = DjangoSettings.SECRET_KEY

DEBUG = not DjangoSettings.IS_PRODUCTION

ALLOWED_HOSTS = DjangoSettings.ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS = DjangoSettings.CSRF_TRUSTED_ORIGINS

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

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
