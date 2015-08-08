# Django settings for projects project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG
DBLOG_CATCH_404_ERRORS = True

ADMINS = (
  ('Andrei Scheinkman', 'andrei@nytimes.com'),
  ('Derek Willis', 'dwillis@nytimes.com')
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'projects'             # Or path to database file if using sqlite3.
DATABASE_USER = 'intuser'             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = 'localhost'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

GEOIP_PATH = '/home/dwillis/geoip'

CACHE_BACKEND = 'file:///var/tmp/django_cache'
CACHE_MIDDLEWARE_SECONDS = 60*5
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

EMAIL_HOST = ''
APPEND_SLASH = True

#GDAL_LIBRARY_PATH = '/usr/local/lib/libgdal.so'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/home/django_trunk/django/contrib/admin/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'p7$qt3_^q53q_n!sl%^(@#xa(13-jefrt05u%bj*8v(cc*m%=o'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
)

ROOT_URLCONF = 'projects.urls'

TEMPLATE_DIRS = (
    '/home/andrei/projects/represents/templates',
    '/home/dwillis/projects/represents/templates',
    '/home/dwillis/django-trunk/django/contrib/gis/templates',
    '/home/django-trunk/django/contrib/gis/templates',
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'projects.represent',
)

# Error emails
if (not DEBUG):
  DEFAULT_FROM_EMAIL = 'andrei@nytimes.com'
  SERVER_EMAIL = 'andrei@nytimes.com'
  SEND_BROKEN_LINK_EMAILS = False
