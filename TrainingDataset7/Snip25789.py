def test_in_bulk_values_list_fields_id(self):
        arts = Article.objects.values_list("id").in_bulk([self.a1.pk, self.a2.pk])
        self.assertEqual(
            arts,
            {
                self.a1.pk: (self.a1.pk,),
                self.a2.pk: (self.a2.pk,),
            },
        )