from django.contrib import admin
from djangodblog.models import ErrorBatch, Error

class ErrorAdmin(admin.ModelAdmin):
    list_display    = ('class_name', 'message', 'datetime', 'traceback')
    list_filter     = ('class_name', 'datetime', 'server_name')
    ordering        = ('-datetime',)

admin.site.register(Error, ErrorAdmin)