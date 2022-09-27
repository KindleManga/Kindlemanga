import re
import logging

from django.core import files
from django.utils.text import slugify

from manga.models import Chapter, Manga, Volume
from manga.utils import image_to_bytesio

logger = logging.getLogger(__name__)


class MangaCrawlerPipeline(object):
    def chap_number(self, chap_name):
        if "Chapter " in chap_name or "Chap " in chap_name:
            chap_numb = re.findall(r"Chapter \d+|Chap \d+", chap_name)
            numb = chap_numb[0].replace("Chapter ", "").replace("Chap ", "")
            return numb
        else:
            numbs = re.findall(r"(\d+(?:\.\d+)?)", chap_name)
            return numbs[-1]

    def process_item(self, item, spider):
        if not item:
            return
        if Manga.objects.filter(
            name=item["name"][0], source=item["source"][0]
        ).exists():
            logger.info("Manga existed")
            return item

        manga = Manga(
            name=item["name"][0],
            unicode_name=item["unicode_name"][0],
            source=item["source"][0],
            total_chap=item["total_chap"][0],
            image_src=item["image_src"][0],
            description=item["description"][0],
            web_source=item["web_source"][0],
            full=item["full"][0],
        )
        manga.save()

        chapters = item["chapters"][::-1]
        k = enumerate(
            [chapters[x : x + 10] for x in range(0, len(chapters), 10)], start=1
        )
        for i, chaps in k:
            vol = Volume(manga=manga, number=i)
            vol.save()
            Chapter.objects.bulk_create(
                [
                    Chapter(
                        number=self.chap_number(c[0]),
                        volume=vol,
                        name=c[0],
                        source=c[1],
                    )
                    for c in chaps
                ]
            )
            logger.debug("Volume added")

        try:
            thumbnail = image_to_bytesio(item["image_src"][0])
            manga.thumbnail.save(f"{slugify(manga.name)}.jpg", files.File(thumbnail))
            logger.info(
                "Manga {} added. Source: {}".format(
                    item["name"][0], item["web_source"][0]
                )
            )
        except Exception as e:
            print("Can not download thumbnail")
        return item
