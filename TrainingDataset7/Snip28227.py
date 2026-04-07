def test_blank_in_grouped_choices(self):
        choices = [
            ("f", "Foo"),
            ("b", "Bar"),
            (
                "Group",
                [
                    ("", "No Preference"),
                    ("fg", "Foo"),
                    ("bg", "Bar"),
                ],
            ),
        ]
        f = models.CharField(choices=choices)
        self.assertEqual(f.get_choices(include_blank=True), choices)