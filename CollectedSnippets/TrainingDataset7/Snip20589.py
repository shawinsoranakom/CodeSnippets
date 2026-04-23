def test_basic(self):
        Author.objects.create(name="Jayden")
        Author.objects.create(name="John Smith", alias="smithj", goes_by="John")
        Author.objects.create(name="Margaret", goes_by="Maggie")
        Author.objects.create(name="Rhonda", alias="adnohR")
        authors = Author.objects.annotate(joined=Concat("alias", "goes_by"))
        self.assertQuerySetEqual(
            authors.order_by("name"),
            [
                "",
                "smithjJohn",
                "Maggie",
                "adnohR",
            ],
            lambda a: a.joined,
        )