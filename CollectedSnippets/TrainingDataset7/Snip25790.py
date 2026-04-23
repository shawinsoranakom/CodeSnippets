def test_in_bulk_values_list_named(self):
        arts = Article.objects.values_list(named=True).in_bulk([self.a1.pk, self.a2.pk])
        self.assertIsInstance(arts, dict)
        self.assertEqual(len(arts), 2)
        arts1 = arts[self.a1.pk]
        self.assertEqual(
            arts1._fields, ("pk", "id", "headline", "pub_date", "author_id", "slug")
        )
        self.assertEqual(arts1.pk, self.a1.pk)
        self.assertEqual(arts1.headline, "Article 1")
        self.assertEqual(arts1.pub_date, self.a1.pub_date)
        self.assertEqual(arts1.author_id, self.au1.pk)
        self.assertEqual(arts1.slug, "a1")