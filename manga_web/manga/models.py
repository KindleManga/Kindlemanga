from django.db import models
from django.urls import reverse
from django.template.defaultfilters import slugify

from unidecode import unidecode


class Manga(models.Model):
    BLOG_TRUYEN = 'blogtruyen'
    NET_TRUYEN = 'nettruyen'
    MANGA_SEE_ONLINE = 'mangaseeonline'

    SOURCE_CHOICES = (
        (BLOG_TRUYEN, 'blogtruyen'),
        (NET_TRUYEN, 'nettruyen'),
        (MANGA_SEE_ONLINE, 'mangaseeonline')
    )

    name = models.TextField(null=False)
    web_source = models.CharField(max_length=200, choices=SOURCE_CHOICES)
    source = models.TextField(null=False)
    description = models.TextField(null=True)
    total_chap = models.IntegerField(null=True)
    image_src = models.TextField(null=True)
    slug = models.SlugField(max_length=255)
    full = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if not self.slug:
            slug = slugify('{} {}'.format(unidecode(self.name), self.web_source))
            if Manga.objects.filter(slug=slug).exists():
                import random
                import string
                slug = slug + " " + ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            self.slug = slug
        super(Manga, self).save(*args, **kwargs)

    def as_dict(self):
        return {'name': self.name, 'slug': self.slug, 'image': self.image_src, 'source': self.web_source}

    def get_absolute_url(self):
        return reverse('manga:detail', kwargs={'slug': self.slug})


class Volume(models.Model):
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE)
    number = models.IntegerField(null=True)
    download_link = models.TextField(null=True)
    fshare_link = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - Volume {} - {}".format(self.manga.name, self.number, self.manga.web_source.upper())

    @property
    def first_chapter(self):
        return self.chapter_set.first()

    @property
    def last_chapter(self):
        return self.chapter_set.last()


class Chapter(models.Model):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    name = models.TextField()
    source = models.TextField()

    def __str__(self):
        return "{} - Volume {} - {}".format(
            self.volume.manga.name,
            self.volume.number,
            self.name
        )

    @property
    def web_source(self):
        return self.volume.manga.web_source
