def test_nested_function_ordering(self):
        Author.objects.create(name="John Smith")
        Author.objects.create(name="Rhonda Simpson", alias="ronny")

        authors = Author.objects.order_by(Length(Coalesce("alias", "name")))
        self.assertQuerySetEqual(
            authors,
            [
                "Rhonda Simpson",
                "John Smith",
            ],
            lambda a: a.name,
        )

        authors = Author.objects.order_by(Length(Coalesce("alias", "name")).desc())
        self.assertQuerySetEqual(
            authors,
            [
                "John Smith",
                "Rhonda Simpson",
            ],
            lambda a: a.name,
        )