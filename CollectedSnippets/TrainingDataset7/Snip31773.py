def test_serialize_prefetch_related_m2m(self):
        # One query for the Article table, one for each prefetched m2m
        # field, and one extra one for the nested prefetch for the Topics
        # that have a relationship to the Category.
        with self.assertNumQueries(5):
            serializers.serialize(
                self.serializer_name,
                Article.objects.prefetch_related(
                    "meta_data",
                    "topics",
                    Prefetch(
                        "categories",
                        queryset=Category.objects.prefetch_related("topic_set"),
                    ),
                ),
            )
        # One query for the Article table, and three m2m queries for each
        # article.
        with self.assertNumQueries(7):
            serializers.serialize(self.serializer_name, Article.objects.all())