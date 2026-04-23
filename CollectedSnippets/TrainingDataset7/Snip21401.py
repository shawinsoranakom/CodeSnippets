def test_subquery_in_filter(self):
        inner = Company.objects.filter(ceo=OuterRef("pk")).values("based_in_eu")
        self.assertSequenceEqual(
            Employee.objects.filter(Subquery(inner)),
            [self.foobar_ltd.ceo],
        )