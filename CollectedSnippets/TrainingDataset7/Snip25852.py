def test_pattern_lookups_with_substr(self):
        a = Author.objects.create(name="John Smith", alias="Johx")
        b = Author.objects.create(name="Rhonda Simpson", alias="sonx")
        tests = (
            ("startswith", [a]),
            ("istartswith", [a]),
            ("contains", [a, b]),
            ("icontains", [a, b]),
            ("endswith", [b]),
            ("iendswith", [b]),
        )
        for lookup, result in tests:
            with self.subTest(lookup=lookup):
                authors = Author.objects.filter(
                    **{"name__%s" % lookup: Substr("alias", 1, 3)}
                )
                self.assertCountEqual(authors, result)