def test_expressions(self):
        authors = Author.objects.annotate(
            name_part=Left("name", Value(3, output_field=IntegerField()))
        )
        self.assertQuerySetEqual(
            authors.order_by("name"), ["Joh", "Rho"], lambda a: a.name_part
        )