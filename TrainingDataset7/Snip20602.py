def test_ordering(self):
        Author.objects.create(name="John Smith", alias="smithj")
        Author.objects.create(name="John Smith", alias="smithj1")
        Author.objects.create(name="Rhonda", alias="ronny")
        authors = Author.objects.order_by(Length("name"), Length("alias"))
        self.assertQuerySetEqual(
            authors,
            [
                ("Rhonda", "ronny"),
                ("John Smith", "smithj"),
                ("John Smith", "smithj1"),
            ],
            lambda a: (a.name, a.alias),
        )