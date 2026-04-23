def test_in_bulk_values_alternative_field_name(self):
        arts = Article.objects.values("headline").in_bulk(
            [self.a1.slug], field_name="slug"
        )
        self.assertEqual(
            arts,
            {self.a1.slug: {"headline": "Article 1"}},
        )