def test_values_no_field_names(self):
        # If you don't specify field names to values(), all are returned.
        self.assertSequenceEqual(
            Article.objects.filter(id=self.a5.id).values(),
            [
                {
                    "id": self.a5.id,
                    "author_id": self.au2.id,
                    "headline": "Article 5",
                    "pub_date": datetime(2005, 8, 1, 9, 0),
                    "slug": "a5",
                }
            ],
        )