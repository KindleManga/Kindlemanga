from django_elasticsearch_dsl import DocType, Index

from .models import Manga

# Name of the Elasticsearch index
manga = Index("mangas")

# See Elasticsearch Indices API reference for available settings
manga.settings(number_of_shards=1, number_of_replicas=0)


@manga.doc_type
class MangaDocument(DocType):
    class Meta:
        model = Manga  # The model associated with this DocType

        # The fields of the model you want to be indexed in Elasticsearch
        fields = [
            "name",
            "web_source",
        ]
