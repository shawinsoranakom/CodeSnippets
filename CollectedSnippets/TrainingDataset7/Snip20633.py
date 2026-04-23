def test_expressions(self):
        authors = Author.objects.annotate(
            name_part=Right("name", Value(3, output_field=IntegerField()))
        )
        self.assertQuerySetEqual(
            authors.order_by("name"), ["ith", "nda"], lambda a: a.name_part
        )