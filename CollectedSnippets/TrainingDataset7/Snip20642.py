def test_basic(self):
        authors = (
            Author.objects.annotate(
                sha256_alias=SHA256("alias"),
            )
            .values_list("sha256_alias", flat=True)
            .order_by("pk")
        )
        self.assertSequenceEqual(
            authors,
            [
                "ef61a579c907bbed674c0dbcbcf7f7af8f851538eef7b8e58c5bee0b8cfdac4a",
                "6e4cce20cd83fc7c202f21a8b2452a68509cf24d1c272a045b5e0cfc43f0d94e",
                "3ad2039e3ec0c88973ae1c0fce5a3dbafdd5a1627da0a92312c54ebfcf43988e",
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                (
                    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                    if connection.features.interprets_empty_strings_as_nulls
                    else None
                ),
            ],
        )