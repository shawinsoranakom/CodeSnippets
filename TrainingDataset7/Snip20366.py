def test_basic(self):
        authors = Author.objects.annotate(nullif=NullIf("alias", "name")).values_list(
            "nullif"
        )
        self.assertCountEqual(
            authors,
            [
                ("smithj",),
                (
                    (
                        ""
                        if connection.features.interprets_empty_strings_as_nulls
                        else None
                    ),
                ),
            ],
        )