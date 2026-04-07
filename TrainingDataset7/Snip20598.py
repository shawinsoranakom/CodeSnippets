def test_basic(self):
        authors = Author.objects.annotate(name_part=Left("name", 5))
        self.assertQuerySetEqual(
            authors.order_by("name"), ["John ", "Rhond"], lambda a: a.name_part
        )
        # If alias is null, set it to the first 2 lower characters of the name.
        Author.objects.filter(alias__isnull=True).update(alias=Lower(Left("name", 2)))
        self.assertQuerySetEqual(
            authors.order_by("name"), ["smithj", "rh"], lambda a: a.alias
        )