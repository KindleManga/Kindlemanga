from django.core.management.base import BaseCommand
from django.utils import timezone

from manga.models import Manga, Volume
from manga.tasks import make_volume


class Command(BaseCommand):
    help = "Convert all vols of given manga id"

    def add_arguments(self, parser):
        parser.add_argument("id", type=int, help="Manga ID")

    def handle(self, *args, **kwargs):
        manga_id = kwargs["id"]
        for v in Manga.objects.get(id=manga_id).volumes.filter(file__in=["", None]):
            make_volume(v.id)
        self.stdout.write(f"Manga {manga_id} converted")
