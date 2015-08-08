from django.contrib.gis import admin
from projects.represent.models import Office, Official, Story, Post, Borough, BlogrunnerItem, Source

class OfficeAdmin(admin.OSMGeoAdmin):
    list_display = ('name', 'district')
    ordering = ('name',)
    fieldsets = (
       ('Location Attributes', {'fields': (('name', 'district', 'description', 'boroughs'))}),
       ('Editable Map View', {'fields': ('poly',)}),
    )
    
    scrollable = False
    map_width = 700
    map_height = 325

class OfficialAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('first_name','last_name')}
    list_display = ('display_name', 'party', 'office', 'gender', 'start_year', 'end_year', 'has_times_topic_url')
    list_filter = ('is_active', 'party', 'gender', 'end_year', 'start_year')
    search_fields = ['last_name']

class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'date', 'created', 'has_thumbnail')
    ordering = ('-created',)

class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'date', 'created', 'has_thumbnail')
    ordering = ('-created',)

class BoroughAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

class BlogrunnerItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'date', 'source', 'created')
    ordering = ('-created',)

class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'category', 'hidden', 'is_local', 'posts')
    list_filter = ('hidden','is_local')
    ordering = ('name',)
    search_fields = ['name']

admin.site.register(Office, admin.GeoModelAdmin)
admin.site.register(Official, OfficialAdmin)
admin.site.register(Story, StoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Borough, BoroughAdmin)
admin.site.register(BlogrunnerItem, BlogrunnerItemAdmin)
admin.site.register(Source, SourceAdmin)
