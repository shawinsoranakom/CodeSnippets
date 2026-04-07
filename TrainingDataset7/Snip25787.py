def test_in_bulk_values_list_fields_including_pk(self):
        arts = Article.objects.values_list("pk", "headline").in_bulk(
            [self.a1.pk, self.a2.pk]
        )
        self.assertEqual(
            arts,
            {
                self.a1.pk: (self.a1.pk, "Article 1"),
                self.a2.pk: (self.a2.pk, "Article 2"),
            },
        )