def test_basic(self):
        authors = (
            Author.objects.annotate(
                sha224_alias=SHA224("alias"),
            )
            .values_list("sha224_alias", flat=True)
            .order_by("pk")
        )
        self.assertSequenceEqual(
            authors,
            [
                "a61303c220731168452cb6acf3759438b1523e768f464e3704e12f70",
                "2297904883e78183cb118fc3dc21a610d60daada7b6ebdbc85139f4d",
                "eba942746e5855121d9d8f79e27dfdebed81adc85b6bf41591203080",
                "d14a028c2a3a2bc9476102bb288234c415a2b01f828ea62ac5b3e42f",
                (
                    "d14a028c2a3a2bc9476102bb288234c415a2b01f828ea62ac5b3e42f"
                    if connection.features.interprets_empty_strings_as_nulls
                    else None
                ),
            ],
        )