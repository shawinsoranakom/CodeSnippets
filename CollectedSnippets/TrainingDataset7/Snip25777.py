def test_in_bulk_values_all(self):
        Article.objects.exclude(pk__in=[self.a1.pk, self.a2.pk]).delete()
        arts = Article.objects.values().in_bulk()
        self.assertEqual(
            arts,
            {
                self.a1.pk: {
                    "id": self.a1.pk,
                    "author_id": self.au1.pk,
                    "headline": "Article 1",
                    "pub_date": self.a1.pub_date,
                    "slug": "a1",
                },
                self.a2.pk: {
                    "id": self.a2.pk,
                    "author_id": self.au1.pk,
                    "headline": "Article 2",
                    "pub_date": self.a2.pub_date,
                    "slug": "a2",
                },
            },
        )