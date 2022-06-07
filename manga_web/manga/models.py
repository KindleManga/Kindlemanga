from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from unidecode import unidecode
from django.utils.text import slugify
from django_extensions.db.models import TimeStampedModel


class Manga(TimeStampedModel):
    class Source(models.TextChoices):
        DOCTRUYEN3Q = "doctruyen3q"
        NETTRUYEN = "nettruyen"
        MANGASEEONLINE = "mangaseeonline"

    name = models.TextField(null=False)
    thumbnail = models.ImageField(null=True, upload_to="manga/thumbnail")
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

    def souce_color(self):
        if self.web_source == "doctruyen3q":
            return "#7858A6"
        elif self.web_source == "nettruyen":
            return "black"
        elif self.web_source == "mangaseeonline":
            return "coral"

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
    return f"{instance.manga.id}/{instance.id}/{filename}"


class Volume(TimeStampedModel):
    manga = models.ForeignKey(
        Manga, on_delete=models.CASCADE, related_name="volumes")
    number = models.CharField(null=True, max_length=10)
    file = models.FileField(upload_to=manga_directory_path, null=True)
    converting = models.BooleanField(default=False)

    def __str__(self):
        return f"<Volume {self.number}>"

    def title(self):
        return f"{self.manga.name} - Volume {self.number}"


class Chapter(TimeStampedModel):
    volume = models.ForeignKey(
        Volume, on_delete=models.CASCADE, related_name="chapters")
    number = models.CharField(null=True, max_length=10)
    name = models.TextField()
    source = models.TextField()

    def __str__(self):
        return f"<Chapter {self.name}>"
