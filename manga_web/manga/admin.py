from django.contrib import admin
from .models import Manga, Chapter, Volume

class MangaAdmin(admin.ModelAdmin):
    pass


class VolumeAdmin(admin.ModelAdmin):
    pass


class ChapterAdmin(admin.ModelAdmin):
    pass


admin.site.register(Manga, MangaAdmin)
admin.site.register(Volume, VolumeAdmin)
admin.site.register(Chapter, ChapterAdmin)
