def test_combined_with_length(self):
        Author.objects.create(name="Rhonda", alias="john_smith")
        Author.objects.create(name="♥♣♠", alias="bytes")
        authors = Author.objects.annotate(filled=LPad("name", Length("alias")))
        self.assertQuerySetEqual(
            authors.order_by("alias"),
            ["  ♥♣♠", "    Rhonda"],
            lambda a: a.filled,
        )