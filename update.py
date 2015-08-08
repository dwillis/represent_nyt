from django.core.management import setup_environ
import settings
setup_environ(settings)

import projects.represent.dataimport

projects.represent.dataimport.update()
