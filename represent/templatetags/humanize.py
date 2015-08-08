import datetime
import time
from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def humanize_array(value):
    ''' ["foo", "bar", "zip"] => "foo, bar and zip" '''
    if len(value) == 0:
        return ""
    elif len(value) == 1:
        return value[0]
    else:
        s = ", ".join(value[:-1])
        return "%s and %s" % (s, value[-1])

@register.filter
def humanize_your_official_list(officials):
    if len(officials) == 2 and reduce(lambda b, o: (b and o.office.name == 'U.S. Senate'), officials, True):
        return mark_safe("Your Senators " + humanize_array([ ("<strong>%s</strong>" % o.display_name()) for o in officials ]))
    return mark_safe(humanize_array([ "your " + o.get_gender_title() + " " + ("<strong>%s</strong>" % o.display_name()) for o in officials ]))

@register.filter
def humanize_your_official_list_without_links(officials):
	if len(officials) == 2 and reduce(lambda b, o: (b and o.office.name == 'U.S. Senate'), officials, True):
		return mark_safe("Your Senators " + humanize_array([ ("<strong>%s</strong>" % o.display_name()) for o in officials ]))
	return mark_safe(humanize_array([ "your " + o.get_gender_title() + " " + ("<strong>%s</strong>" % o.display_name()) for o in officials ]))

@register.filter
def humanize_your_official_list_without_links_or_pronouns(officials):
	if len(officials) == 2 and reduce(lambda b, o: (b and o.office.name == 'U.S. Senate'), officials, True):
		return mark_safe("Your Senators " + humanize_array([ ("<strong>%s</strong>" % o.display_name()) for o in officials ]))
	return mark_safe(humanize_array([ o.get_gender_title() + " " + ("<strong>%s</strong>" % o.display_name()) for o in officials ]))

@register.filter
def humanize_date(d):
    if d == d.today():
        return "Today"
    elif d == d.today() - datetime.timedelta(days=1):
        return "Yesterday"
    elif d.today() - d < datetime.timedelta(days=5):
        return d.strftime("%A")
    elif (d.strftime("%b") == 'May'):
        return d.strftime("%b %d").replace(' 0', ' ')
    else:
        return d.strftime("%b. %d").replace(' 0', ' ')

@register.filter
def sentence(str):
    ''' "foo bar zip." => "Foo bar zip." '''
    return str[0].upper() + str[1:]
sentence.is_safe = True

@register.filter
def to_link(text, url):
    return '<a href="%s">%s</a>' % (conditional_escape(url), conditional_escape(text))

@register.filter
def rfc3999(date):
    """Formats the given date in RFC 3339 format for feeds."""
    if not date: return ''
    date = date + datetime.timedelta(seconds = -time.timezone)
    if time.daylight:
        date += datetime.timedelta(seconds = time.altzone)
    return date.strftime('%m-%d-%YT%H:%M:%SZ')

@register.filter
def trim_title(title):
    i = title.find(';')
    if i > 0:
        return title[:i]
    return title
