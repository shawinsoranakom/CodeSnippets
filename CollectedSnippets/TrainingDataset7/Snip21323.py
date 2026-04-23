def test_chained_values_with_expression(self):
        Employee.objects.create(firstname="Joe", lastname="Jones", salary=2)
        joes = Employee.objects.filter(firstname="Joe").values("firstname")
        self.assertSequenceEqual(
            joes.values("firstname", sum_salary=Sum("salary")),
            [{"firstname": "Joe", "sum_salary": 12}],
        )
        self.assertSequenceEqual(
            joes.values(sum_salary=Sum("salary")), [{"sum_salary": 12}]
        )