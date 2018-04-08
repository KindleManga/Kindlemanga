import logging

from manga.models import Manga, Volume, Chapter

logger = logging.getLogger(__name__)


class MangaCrawlerPipeline(object):
    def process_item(self, item, spider):
        if Manga.objects.filter(name=item['name'][0]):
            logger.info('Manga existed')
            return item

        manga = Manga(
            name=item['name'][0],
            source=item['source'][0],
            total_chap=item['total_chap'][0],
            image_src=item['image_src'][0]
        )
        manga.save()
        logger.info('Manga added')

        chapters = item['chapters']
        k = enumerate(
            [chapters[x:x+12] for x in range(0, len(chapters), 12)],
            start=1
        )
        for i, chaps in k:
            vol = Volume(manga=manga, number=i)
            vol.save()
            Chapter.objects.bulk_create(
                [Chapter(volume=vol, name=c[0], source=c[1]) for c in chaps]
            )
            logger.info('Volume added')
        return item
