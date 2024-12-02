from os.path import join as pjoin, abspath, dirname, pardir

SECRET_KEY = "SECRET"
PROJ_ROOT = abspath(pjoin(dirname(__file__), pardir))
DATA_ROOT = pjoin(PROJ_ROOT, "data")
THUMBNAIL_PREFIX = "test/cache/"
THUMBNAIL_DEBUG = True
THUMBNAIL_LOG_HANDLER = {
    "class": "sorl.thumbnail.log.ThumbnailLogHandler",
    "level": "ERROR",
}
STORAGES = {
    "default": {
        "BACKEND": "tests.test_thumbnails.storage.TestStorage",
    },
}

ADMINS = (("Sorl", "thumbnail@sorl.net"),)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "db.sqlite3",
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
MEDIA_ROOT = pjoin(PROJ_ROOT, "media")
MEDIA_URL = "/media/"
ROOT_URLCONF = "tests.test_thumbnails.urls"
INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "sorl.thumbnail",
    "tests.test_thumbnails",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]
MIDDLEWARE = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)
