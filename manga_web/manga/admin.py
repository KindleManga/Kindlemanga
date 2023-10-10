from django.contrib import admin

from .models import Chapter, Manga, Volume


class MangaAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "web_source", "total_chap", "full"]


class VolumeAdmin(admin.ModelAdmin):
    list_display = ("id", "manga", "number", "file")
    search_fields = ["id", "manga__name"]
    raw_id_fields = [
        "manga",
    ]


class ChapterAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "source")
    raw_id_fields = [
        "volume",
    ]
    search_fields = ["id", "volume__manga__name", "name", "source"]


admin.site.register(Manga, MangaAdmin)
admin.site.register(Volume, VolumeAdmin)
admin.site.register(Chapter, ChapterAdmin)
