import django_filters
from .models import Manga


class MangaFilter(django_filters.FilterSet):
    class Meta:
        model = Manga
        fields = ['web_source', "full"]
        exclude = ['thumbnail']
