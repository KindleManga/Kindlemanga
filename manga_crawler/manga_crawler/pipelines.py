import re
import logging

from manga.models import Chapter, Manga, Volume

logger = logging.getLogger(__name__)


class MangaCrawlerPipeline(object):
    def process_item(self, item, spider):
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
        logger.info(
            "Manga {} added. Source: {}".format(
                item["name"][0], item["web_source"][0])
        )

        chapters = item["chapters"][::-1]
        k = enumerate(
            [chapters[x: x + 10] for x in range(0, len(chapters), 10)], start=1
        )
        for i, chaps in k:
            vol = Volume(manga=manga, number=i)
            vol.save()
            Chapter.objects.bulk_create(
                [Chapter(number=re.findall(r"\d+", c[0])[0],
                         volume=vol, name=c[0], source=c[1]) for c in chaps]
            )
            logger.debug("Volume added")
        return item
