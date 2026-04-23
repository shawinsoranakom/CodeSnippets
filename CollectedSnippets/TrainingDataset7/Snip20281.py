def test_querysets_relational(self):
        """
        Queries across tables, involving primary key
        """
        self.assertSequenceEqual(
            Employee.objects.filter(business__name="Sears"),
            [self.fran, self.dan],
        )
        self.assertSequenceEqual(
            Employee.objects.filter(business__pk="Sears"),
            [self.fran, self.dan],
        )

        self.assertQuerySetEqual(
            Business.objects.filter(employees__employee_code=123),
            [
                "Sears",
            ],
            lambda b: b.name,
        )
        self.assertQuerySetEqual(
            Business.objects.filter(employees__pk=123),
            [
                "Sears",
            ],
            lambda b: b.name,
        )

        self.assertQuerySetEqual(
            Business.objects.filter(employees__first_name__startswith="Fran"),
            [
                "Sears",
            ],
            lambda b: b.name,
        )