def test_values_filter_and_no_fields(self):
        # values() returns a list of dictionaries instead of object instances,
        # and you can specify which fields you want to retrieve.
        self.assertSequenceEqual(
            Article.objects.filter(id__in=(self.a5.id, self.a6.id)).values(),
            [
                {
                    "id": self.a5.id,
                    "headline": "Article 5",
                    "pub_date": datetime(2005, 8, 1, 9, 0),
                    "author_id": self.au2.id,
                    "slug": "a5",
                },
                {
                    "id": self.a6.id,
                    "headline": "Article 6",
                    "pub_date": datetime(2005, 8, 1, 8, 0),
                    "author_id": self.au2.id,
                    "slug": "a6",
                },
            ],
        )