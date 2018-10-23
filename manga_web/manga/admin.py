from django.contrib import admin
from .models import Manga, Chapter, Volume

class MangaAdmin(admin.ModelAdmin):
    pass


class VolumeAdmin(admin.ModelAdmin):
    list_display = ('id', 'manga', 'number', 'download_link', 'fshare_link')
    search_fields = ['id', 'manga__name']
    raw_id_fields = ['manga', ]


class ChapterAdmin(admin.ModelAdmin):
    pass


admin.site.register(Manga, MangaAdmin)
admin.site.register(Volume, VolumeAdmin)
admin.site.register(Chapter, ChapterAdmin)
