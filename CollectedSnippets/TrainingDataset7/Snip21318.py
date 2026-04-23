def test_values_expression(self):
        self.assertSequenceEqual(
            Company.objects.values(salary=F("ceo__salary")),
            [{"salary": 10}, {"salary": 20}, {"salary": 30}],
        )