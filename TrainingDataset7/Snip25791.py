def test_in_bulk_values_list_named_fields(self):
        arts = Article.objects.values_list("pk", "headline", named=True).in_bulk(
            [self.a1.pk, self.a2.pk]
        )
        self.assertIsInstance(arts, dict)
        self.assertEqual(len(arts), 2)
        arts1 = arts[self.a1.pk]
        self.assertEqual(arts1._fields, ("pk", "headline"))
        self.assertEqual(arts1.pk, self.a1.pk)
        self.assertEqual(arts1.headline, "Article 1")