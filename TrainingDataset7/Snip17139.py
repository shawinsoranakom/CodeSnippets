def test_name_expressions(self):
        # Aggregates are spotted correctly from F objects.
        # Note that Adrian's age is 34 in the fixtures, and he has one book
        # so both conditions match one author.
        qs = (
            Author.objects.annotate(Count("book"))
            .filter(Q(name="Peter Norvig") | Q(age=F("book__count") + 33))
            .order_by("name")
        )
        self.assertQuerySetEqual(
            qs, ["Adrian Holovaty", "Peter Norvig"], lambda b: b.name
        )