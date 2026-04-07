def test_querysets(self):
        """
        Both pk and custom attribute_name can be used in filter and friends
        """
        self.assertSequenceEqual(Employee.objects.filter(pk=123), [self.dan])
        self.assertSequenceEqual(Employee.objects.filter(employee_code=123), [self.dan])
        self.assertSequenceEqual(
            Employee.objects.filter(pk__in=[123, 456]),
            [self.fran, self.dan],
        )
        self.assertSequenceEqual(Employee.objects.all(), [self.fran, self.dan])

        self.assertQuerySetEqual(
            Business.objects.filter(name="Sears"), ["Sears"], lambda b: b.name
        )
        self.assertQuerySetEqual(
            Business.objects.filter(pk="Sears"),
            [
                "Sears",
            ],
            lambda b: b.name,
        )