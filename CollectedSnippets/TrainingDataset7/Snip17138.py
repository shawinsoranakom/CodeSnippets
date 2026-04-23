def test_name_filters(self):
        qs = (
            Author.objects.annotate(Count("book"))
            .filter(Q(book__count__exact=2) | Q(name="Adrian Holovaty"))
            .order_by("name")
        )
        self.assertQuerySetEqual(
            qs, ["Adrian Holovaty", "Peter Norvig"], lambda b: b.name
        )