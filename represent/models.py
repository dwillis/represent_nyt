from django.contrib.gis.db import models
from django.contrib import admin
from django.core import urlresolvers
from django.db.models import Count
import datetime

CAT_CHOICES = (
   ('N', 'Newspaper'),
   ('M', 'Magazine'),
   ('B', 'Blog'),
   ('V', 'Video'),
   ('T', 'Twitter'),
   ('A', 'Broadcast'),
)

LEVEL_CHOICES = (
    ('F', 'Federal'),
    ('S', 'State'),
    ('L', 'Local'),
)

ELECTION_CHOICES = (
    ('P', 'Primary'),
    ('G', 'General'),
    ('S', 'Special'),
    ('R', 'Runoff'),
)

class Borough(models.Model):
    name = models.CharField(max_length=25)
    slug = models.SlugField(max_length=25)
    
    def __unicode__(self):
        return self.name

class Office(models.Model):
    name = models.CharField(max_length=75)
    level = models.CharField(max_length=1, choices=LEVEL_CHOICES)
    district = models.IntegerField(null=True, blank=True)
    boroughs = models.ManyToManyField(Borough, blank=True)
    description = models.TextField(null=True, blank=True)
    sort = models.IntegerField()
    poly = models.MultiPolygonField(null=True, blank=True)
    objects = models.GeoManager()
    
    def __unicode__(self):
        if self.id == 159:
            return "Junior Senator"
        if self.id == 160:
            return "Senior Senator"
        if self.name == "Congress":
            return "Congressional District %s" % str(self.district)
        if self.name == "Community Board":
            # 302 => Brooklyn Community Board 2
            borough_number = int((str(self.district))[0:1])
            borough_name = ("Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island")[borough_number - 1]
            board_number = int((str(self.district))[1:])
            return "%s Community Board %d" % (borough_name, board_number)
        if self.district:
            return "%s %s" % (self.name, str(self.district))
        return self.name
    
    def get_place(self):
        if self.name == "Borough President":
            return self.description
        map = {
            "U.S. Senate": "New York",
            "Congress": "Congressional District %s" % self.district,
            "State Senate": "State Senate District %s" % self.district,
            "State Assembly": "State Assembly District %s" % self.district,
            "City Council": "City Council District %s" % self.district
        }
        print dir(self)
        if self.name in map:
            return map[self.name]
        return self.district
    
    def get_body(self):
        map = {
            "U.S. Senate": "U.S. Senate",
            "Congress": "U.S. House of Representatives",
            "State Senate": "New York State Senate",
            "State Assembly": "New York State Assembly",
            "City Council": "New York City Council"
        }
        if self.name in map:
            return map[self.name]
        return ""
    
    def get_body_url(self):
        return {
            "U.S. Senate": "/represent/office/senate/",
            "Congress": "/represent/office/congress/",
            "State Senate": "/represent/office/state-senate/",
            "State Assembly": "/represent/office/state-assembly/",
            "City Council": "/represent/office/city-council/"
        }[self.name]
    
    def get_district_title(self):
        return {
            "U.S. Senate": "U.S. Senators",
            "Congress": "Congressional",
            "State Senate": "New York State Senate",
            "State Assembly": "New York State Assembly",
            "City Council": "New York City Council"
        }[self.name]
        
    def current_official(self):
        return self.official_set.get(is_active=True)
            
    def admin_url(self):
        return "/represent/q/admin/represent/office/%d" % (self.id,)

class Official(models.Model):
    last_name = models.CharField(max_length=120)
    first_name = models.CharField(max_length=90)
    slug = models.CharField(max_length=210)
    gender = models.CharField(max_length=1)
    party = models.CharField(max_length=25)
    congress_id = models.CharField(max_length=7, null=True, blank=True)
    start_year = models.IntegerField()
    end_year = models.IntegerField()
    details = models.TextField(null=True, blank=True)
    office = models.ForeignKey(Office)
    official_url = models.URLField(null=True, blank=True)
    photo_url = models.URLField(null=True, blank=True)
    times_topic_url = models.URLField(null=True, blank=True)
    twitter_rss_url = models.URLField(null=True, blank=True)
    cspan_id = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField()
    
    def display_name(self):
        return "%s %s" % (self.first_name, self.last_name)
    
    def get_absolute_url(self):
        return "/represent/official/%s/" % self.slug
    
    def get_absolute_rss_url(self):
        return "/represent/feeds/official/%d/" % self.id
    
    def get_gender_title(self):
        sex = { 'F': 'woman', 'M': 'man' }[self.gender]
        return {
            "U.S. Senate": "Senator",
            "Congress": "Congress%s" % sex,
            "State Senate": "State Senator",
            "State Assembly": "State Assembly%s" % sex,
            "City Council": "Council%s" % sex,
            "Borough President": "Borough President"
        }[self.office.name]
    
    def get_long_gender_title(self):
        sex = { 'F': 'woman', 'M': 'man' }[self.gender]
        return {
            "U.S. Senate": str(self.office),
            "Congress": "Congress%s" % sex,
            "State Senate": "State Senator",
            "State Assembly": "State Assembly%s" % sex,
            "City Council": "City Council%s" % sex,
            "Borough President": "Borough President"
        }[self.office.name]
    
    def get_honorific(self):
        return { 'F': 'Ms.', 'M': 'Mr.' }[self.gender]
    
    # TODO: Are there any reps that should be Dr., Gen. or Mrs.?
    def get_courtesy_title(self):
        '''
        From the style guide:
        "Use Mr., Mrs., Miss or Ms. with surnames in the news columns for second
        and later references to people who do not bear specialized titles, like
        Dr., Gen. or Gov."
        '''
        return self.get_honorific() + " " + self.last_name
    
    def has_times_topic_url(self):
        if self.times_topic_url:
            return True
        else:
            return False
    
    # http://topics.nytimes.com/top/reference/timestopics/people/s/sheldon_silver/index.html
    # http://www.blogrunner.com/snapshot/t/reference/timestopics/people/s/sheldon_silver/tt.xml
    
    def blogrunner_rss_url(self):
        if self.has_times_topic_url():
            return self.times_topic_url.replace('topics.nytimes.com/top','www.blogrunner.com/snapshot/t').replace('index.html','tt.xml')
        else:
            return None
            
    def admin_url(self):
        return "/represent/q/admin/represent/official/%d" % (self.id,)
    
    def article_count(self, days=30):
        d = datetime.date.today() - datetime.timedelta(days)
        return self.story_set.filter(date__gte=d).aggregate(Count('id'))['id__count']

    def city_room_count(self, days=30):
        d = datetime.date.today() - datetime.timedelta(days)
        return self.post_set.filter(date__gte=d).aggregate(Count('id'))['id__count']

    def blogrunner_count(self, days=30):
        d = datetime.date.today() - datetime.timedelta(days)
        return self.blogrunneritem_set.filter(date__gte=d).aggregate(Count('id'))['id__count']

    def __unicode__(self):
        return "%s %s" % (self.first_name, self.last_name)
    

class Story(models.Model):
    '''An article or editorial from nytimes.com.'''
    officials = models.ManyToManyField(Official)
    url = models.URLField()
    title = models.TextField()
    date = models.DateField()
    thumbnail_url = models.URLField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    def has_thumbnail(self):
        if self.thumbnail_url:
            return True
        else:
            return False
    
    class Meta:
        verbose_name_plural = "stories"

class Post(models.Model):
    '''A City Room blog post.'''
    officials = models.ManyToManyField(Official)
    url = models.URLField()
    title = models.TextField()
    date = models.DateField()
    text = models.TextField()
    quote = models.TextField(null=True, blank=True)
    excerpt = models.TextField()
    thumbnail_url = models.URLField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

    def has_thumbnail(self):
        if self.thumbnail_url:
            return True
        else:
            return False

class Source(models.Model):
    '''A BlogrunnerItem source'''
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    category = models.CharField(max_length=1, choices=CAT_CHOICES, null=True, blank=True)
    hidden = models.BooleanField(default=True)
    is_local = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
    
    def posts(self):
        return len(self.blogrunneritem_set.all())

class BlogrunnerItem(models.Model):
    '''A Blogrunner item'''
    officials = models.ManyToManyField(Official)
    url = models.URLField()
    source = models.ForeignKey(Source)
    title = models.TextField()
    date = models.DateField()
    text = models.TextField()
    thumbnail_url = models.URLField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def has_thumbnail(self):
        if self.thumbnail_url:
            return True
        else:
            return False
