def test_in_bulk_values_list_named_fields_alternative_field(self):
        arts = Article.objects.values_list("headline", named=True).in_bulk(
            [self.a1.slug, self.a2.slug], field_name="slug"
        )
        self.assertEqual(len(arts), 2)
        arts1 = arts[self.a1.slug]
        self.assertEqual(arts1._fields, ("slug", "headline"))
        self.assertEqual(arts1.slug, "a1")
        self.assertEqual(arts1.headline, "Article 1")