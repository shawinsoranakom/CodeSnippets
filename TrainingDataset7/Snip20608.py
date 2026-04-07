def test_basic(self):
        authors = (
            Author.objects.annotate(
                md5_alias=MD5("alias"),
            )
            .values_list("md5_alias", flat=True)
            .order_by("pk")
        )
        self.assertSequenceEqual(
            authors,
            [
                "6117323d2cabbc17d44c2b44587f682c",
                "ca6d48f6772000141e66591aee49d56c",
                "bf2c13bc1154e3d2e7df848cbc8be73d",
                "d41d8cd98f00b204e9800998ecf8427e",
                (
                    "d41d8cd98f00b204e9800998ecf8427e"
                    if connection.features.interprets_empty_strings_as_nulls
                    else None
                ),
            ],
        )