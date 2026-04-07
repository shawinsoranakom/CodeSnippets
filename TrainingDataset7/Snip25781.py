def test_in_bulk_values_fields_pk(self):
        arts = Article.objects.values("pk").in_bulk([self.a1.pk])
        self.assertEqual(
            arts,
            {self.a1.pk: {"pk": self.a1.pk}},
        )