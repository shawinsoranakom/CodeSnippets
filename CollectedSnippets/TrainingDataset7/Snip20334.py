def test_cast_to_text_field(self):
        self.assertEqual(
            Author.objects.values_list(
                Cast("age", models.TextField()), flat=True
            ).get(),
            "1",
        )