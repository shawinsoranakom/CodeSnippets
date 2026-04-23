def test_in_bulk_values_fields(self):
        arts = Article.objects.values("headline").in_bulk([self.a1.pk])
        self.assertEqual(
            arts,
            {self.a1.pk: {"headline": "Article 1"}},
        )