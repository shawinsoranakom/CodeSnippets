def test_many(self):
        Author.objects.create(name="Jayden")
        Author.objects.create(name="John Smith", alias="smithj", goes_by="John")
        Author.objects.create(name="Margaret", goes_by="Maggie")
        Author.objects.create(name="Rhonda", alias="adnohR")
        authors = Author.objects.annotate(
            joined=Concat("name", V(" ("), "goes_by", V(")"), output_field=CharField()),
        )
        self.assertQuerySetEqual(
            authors.order_by("name"),
            [
                "Jayden ()",
                "John Smith (John)",
                "Margaret (Maggie)",
                "Rhonda ()",
            ],
            lambda a: a.joined,
        )