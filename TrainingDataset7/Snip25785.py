def test_in_bulk_values_list_all(self):
        Article.objects.exclude(pk__in=[self.a1.pk, self.a2.pk]).delete()
        arts = Article.objects.values_list().in_bulk()
        self.assertEqual(
            arts,
            {
                self.a1.pk: (
                    self.a1.pk,
                    "Article 1",
                    self.a1.pub_date,
                    self.au1.pk,
                    "a1",
                ),
                self.a2.pk: (
                    self.a2.pk,
                    "Article 2",
                    self.a2.pub_date,
                    self.au1.pk,
                    "a2",
                ),
            },
        )