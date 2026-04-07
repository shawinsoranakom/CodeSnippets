def test_values_annotate_values(self):
        qs = (
            Book.objects.values("name")
            .annotate(n_authors=Count("authors"))
            .values_list("pk", flat=True)
            .order_by("name")
        )
        self.assertEqual(list(qs), list(Book.objects.values_list("pk", flat=True)))