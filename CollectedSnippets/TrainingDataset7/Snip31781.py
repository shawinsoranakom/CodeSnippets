def test_deterministic_mapping_ordering(self):
        """
        Mapping such as fields should be deterministically ordered. (#24558)
        """
        output = serializers.serialize(self.serializer_name, [self.a1], indent=2)
        categories = self.a1.categories.values_list("pk", flat=True)
        self.assertEqual(
            output,
            self.mapping_ordering_str
            % {
                "article_pk": self.a1.pk,
                "author_pk": self.a1.author_id,
                "first_category_pk": categories[0],
                "second_category_pk": categories[1],
            },
        )