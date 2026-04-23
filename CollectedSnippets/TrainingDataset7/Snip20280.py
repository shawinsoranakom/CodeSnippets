def test_querysets_related_name(self):
        """
        Custom pk doesn't affect related_name based lookups
        """
        self.assertSequenceEqual(
            self.business.employees.all(),
            [self.fran, self.dan],
        )
        self.assertQuerySetEqual(
            self.fran.business_set.all(),
            [
                "Sears",
            ],
            lambda b: b.name,
        )