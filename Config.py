from os import environ as env

class DjangoSettings:
    ALLOWED_HOSTS = env.get("ALLOWED_HOSTS", "127.0.0.1").split("||")
    CSRF_TRUSTED_ORIGINS = env.get("CSRF_TRUSTED_ORIGINS", "http://127.0.0.1:8000").split("||")
    SECRET_KEY = env.get("SECRET_KEY", "test-secret-key")
    IS_PRODUCTION = int(env.get("IS_PRODUCTION", 0))
    if IS_PRODUCTION:
        STATIC_ROOT = env.get("STATIC_ROOT", "")
    else:
        STATICFILES_DIRS = env.get("STATICFILES_DIRS", []).split("||")

class DatabaseSettings:
    DATABASE_ENGINE = env.get("DATABASE_ENGINE", "django.db.backends.sqlite3")
    DATABASE_NAME = env.get("DATABASE_NAME", "db.sqlite3")
    DATABASE_USER = env.get("DATABASE_USER", None)
    DATABASE_PASSWORD = env.get("DATABASE_PASSWORD", None)
    DATABASE_HOST = env.get("DATABASE_HOST", None)
    DATABASE_PORT = int(env.get("DATABASE_PORT", 3306))
    