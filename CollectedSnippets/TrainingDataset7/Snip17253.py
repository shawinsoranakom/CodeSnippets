def test_alias_after_values(self):
        qs = Book.objects.values_list("pk").alias(other_pk=F("pk"))
        self.assertEqual(qs.get(pk=self.b1.pk), (self.b1.pk,))