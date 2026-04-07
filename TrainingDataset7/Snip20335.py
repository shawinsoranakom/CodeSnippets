def test_basic(self):
        Author.objects.create(name="John Smith", alias="smithj")
        Author.objects.create(name="Rhonda")
        authors = Author.objects.annotate(display_name=Coalesce("alias", "name"))
        self.assertQuerySetEqual(
            authors.order_by("name"), ["smithj", "Rhonda"], lambda a: a.display_name
        )