def test_annotate_values_filter(self):
        companies = (
            Company.objects.annotate(
                foo=RawSQL("%s", ["value"]),
            )
            .filter(foo="value")
            .order_by("name")
        )
        self.assertSequenceEqual(
            companies,
            [self.example_inc, self.foobar_ltd, self.gmbh],
        )