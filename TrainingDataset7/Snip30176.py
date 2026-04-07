def test_named_values_list(self):
        qs = Author.objects.prefetch_related("books")
        self.assertCountEqual(
            [value.name for value in qs.values_list("name", named=True)],
            ["Anne", "Charlotte", "Emily", "Jane"],
        )