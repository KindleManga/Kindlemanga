from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from unidecode import unidecode
from django_extensions.db.models import TimeStampedModel


class Manga(TimeStampedModel):
    class Source(models.TextChoices):
        VLOGTRUYEN = "vlogtruyen"
        MANGASEEONLINE = "mangaseeonline"

    name = models.TextField(null=False)
    unicode_name = models.TextField(null=True)
    web_source = models.CharField(max_length=200, choices=Source.choices)
    source = models.TextField(null=False)
    description = models.TextField(null=True)
    total_chap = models.IntegerField(null=True)
    image_src = models.TextField(null=True)
    slug = models.SlugField(max_length=255)
    full = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if not self.slug:
            slug = slugify("{} {}".format(
                unidecode(self.name), self.web_source))
            if Manga.objects.filter(slug=slug).exists():
                import random
                import string

                slug = (
                    slug
                    + " "
                    + "".join(
                        random.choice(string.ascii_uppercase + string.digits)
                        for _ in range(6)
                    )
                )
            self.slug = slug
        super(Manga, self).save(*args, **kwargs)

    def as_dict(self):
        return {
            "name": self.name,
            "slug": self.slug,
            "image": self.image_src,
            "source": self.web_source,
        }

    def get_absolute_url(self):
        return reverse("manga:detail", kwargs={"slug": self.slug})


def manga_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return f"{instance.manga.name}/volume_{instance.author.id}/{filename}"


class Volume(TimeStampedModel):
    manga = models.ForeignKey(
        Manga, on_delete=models.CASCADE, related_name="volumes")
    number = models.IntegerField(null=True)
    file = models.FileField(upload_to=manga_directory_path, null=True)

    def __str__(self):
        return "{} - Volume {} - {}".format(
            self.manga.name, self.number, self.manga.web_source.upper()
        )

    @property
    def first_chapter(self):
        return self.chapters.first()

    @property
    def last_chapter(self):
        return self.chapters.last()


class Chapter(TimeStampedModel):
    volume = models.ForeignKey(
        Volume, on_delete=models.CASCADE, related_name="chapters")
    number = models.IntegerField(null=True)
    name = models.TextField()
    source = models.TextField()

    def __str__(self):
        return "{} - Volume {} - {}".format(
            self.volume.manga.name, self.volume.number, self.name
        )

    @property
    def web_source(self):
        return self.volume.manga.web_source
