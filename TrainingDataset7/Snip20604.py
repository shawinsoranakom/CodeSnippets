def test_basic(self):
        Author.objects.create(name="John Smith", alias="smithj")
        Author.objects.create(name="Rhonda")
        authors = Author.objects.annotate(lower_name=Lower("name"))
        self.assertQuerySetEqual(
            authors.order_by("name"), ["john smith", "rhonda"], lambda a: a.lower_name
        )
        Author.objects.update(name=Lower("name"))
        self.assertQuerySetEqual(
            authors.order_by("name"),
            [
                ("john smith", "john smith"),
                ("rhonda", "rhonda"),
            ],
            lambda a: (a.lower_name, a.name),
        )