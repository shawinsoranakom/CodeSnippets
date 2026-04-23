def test_in_bulk_with_field(self):
        self.assertEqual(
            Article.objects.in_bulk(
                [self.a1.slug, self.a2.slug, self.a3.slug], field_name="slug"
            ),
            {
                self.a1.slug: self.a1,
                self.a2.slug: self.a2,
                self.a3.slug: self.a3,
            },
        )