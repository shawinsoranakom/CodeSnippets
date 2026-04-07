def test_values(self):
        self.assertSequenceEqual(
            Company.objects.annotate(negated=~F("based_in_eu"))
            .values_list("name", "negated")
            .order_by("name"),
            [("Example Inc.", False), ("Foobar Ltd.", True)],
        )