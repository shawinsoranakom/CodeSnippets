def test_values_list_flat_order_by(self):
        self.assertSequenceEqual(
            Article.objects.values_list("id", flat=True).order_by("id"),
            [
                self.a1.id,
                self.a2.id,
                self.a3.id,
                self.a4.id,
                self.a5.id,
                self.a6.id,
                self.a7.id,
            ],
        )