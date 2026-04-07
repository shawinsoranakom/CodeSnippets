def test_in_bulk_values_fields_id(self):
        arts = Article.objects.values("id").in_bulk([self.a1.pk])
        self.assertEqual(
            arts,
            {self.a1.pk: {"id": self.a1.pk}},
        )