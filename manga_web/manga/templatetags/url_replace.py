from urllib.parse import urlencode
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    query = context["request"].GET.copy()
    if query.get("page"):
        query.pop("page")
    query.update(kwargs)
    return query.urlencode()
