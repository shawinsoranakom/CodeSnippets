def test_values_list_single_field(self):
        self.assertSequenceEqual(
            Article.objects.values_list("headline"),
            [
                ("Article 5",),
                ("Article 6",),
                ("Article 4",),
                ("Article 2",),
                ("Article 3",),
                ("Article 7",),
                ("Article 1",),
            ],
        )