from django.core.management.base import BaseCommand
from django.utils import timezone

from manga.models import Volume
from manga.tasks import make_volume


class Command(BaseCommand):
    help = "Remove `converting` status for all converting volumes"

    def handle(self, *args, **kwargs):
        for v in Volume.objects.filter(converting=True):
            v.converting = False
            v.save()
        self.stdout.write(
            f"Successfully removed converting status for all volumes")
