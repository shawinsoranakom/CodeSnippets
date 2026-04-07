def test_in_bulk_values_pks(self):
        arts = Article.objects.values().in_bulk([self.a1.pk])
        self.assertEqual(
            arts,
            {
                self.a1.pk: {
                    "id": self.a1.pk,
                    "author_id": self.au1.pk,
                    "headline": "Article 1",
                    "pub_date": self.a1.pub_date,
                    "slug": "a1",
                }
            },
        )