def test_values_list_flat_no_fields(self):
        with ignore_warnings(category=RemovedInDjango70Warning):
            qs = Article.objects.values_list(flat=True)
        self.assertSequenceEqual(
            qs,
            [
                self.a5.id,
                self.a6.id,
                self.a4.id,
                self.a2.id,
                self.a3.id,
                self.a7.id,
                self.a1.id,
            ],
        )