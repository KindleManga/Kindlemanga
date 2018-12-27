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

    name = models.CharField(max_length=500, null=False)
    web_source = models.CharField(max_length=100, choices=SOURCE_CHOICES)
    source = models.URLField(max_length=500, null=False)
    description = models.TextField(null=True)
    total_chap = models.IntegerField(null=True)
    image_src = models.URLField(max_length=500, null=True)
    slug = models.SlugField()
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
        return {'name': self.name, 'slug': self.slug, 'image': self.image_src}

    def get_absolute_url(self):
        return reverse('manga:detail', kwargs={'slug': self.slug})


class Volume(models.Model):
    manga = models.ForeignKey(Manga, on_delete=models.CASCADE)
    number = models.IntegerField(null=True)
    download_link = models.URLField(max_length=500, null=True)
    fshare_link = models.URLField(max_length=500, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} - Volume {}".format(self.manga.name, self.number)


class Chapter(models.Model):
    volume = models.ForeignKey(Volume, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    source = models.URLField(max_length=500)

    def __str__(self):
        return "{} - Volume {} - {}".format(
            self.volume.manga.name,
            self.volume.number,
            self.name
        )
