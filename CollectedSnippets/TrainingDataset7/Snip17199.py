def test_values_with_pk_annotation(self):
        # annotate references a field in values() with pk
        publishers = Publisher.objects.values("id", "book__rating").annotate(
            total=Sum("book__rating")
        )
        for publisher in publishers.filter(pk=self.p1.pk):
            self.assertEqual(publisher["book__rating"], publisher["total"])