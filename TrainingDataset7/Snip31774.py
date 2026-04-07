def test_serialize_prefetch_related_m2m_with_natural_keys(self):
        # One query for the Article table, one for each prefetched m2m
        # field, and a query to get the categories for each Article (two in
        # total).
        with self.assertNumQueries(5):
            serializers.serialize(
                self.serializer_name,
                Article.objects.prefetch_related(
                    Prefetch(
                        "meta_data",
                        queryset=CategoryMetaData.objects.prefetch_related(
                            "category_set"
                        ),
                    ),
                    "topics",
                ),
                use_natural_foreign_keys=True,
            )