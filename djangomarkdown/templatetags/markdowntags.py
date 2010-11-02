from markdown import Markdown
from django import template

from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

md = Markdown()
register = template.Library()

@register.filter
def markdown(text, autoescape=None):
    result = md.convert(text)
    return mark_safe(result)
markdown.needs_autoescape = True
