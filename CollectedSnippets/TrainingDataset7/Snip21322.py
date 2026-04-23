def test_values_expression_group_by(self):
        # values() applies annotate() first, so values selected are grouped by
        # id, not firstname.
        Employee.objects.create(firstname="Joe", lastname="Jones", salary=2)
        joes = Employee.objects.filter(firstname="Joe")
        self.assertSequenceEqual(
            joes.values("firstname", sum_salary=Sum("salary")).order_by("sum_salary"),
            [
                {"firstname": "Joe", "sum_salary": 2},
                {"firstname": "Joe", "sum_salary": 10},
            ],
        )
        self.assertSequenceEqual(
            joes.values("firstname").annotate(sum_salary=Sum("salary")),
            [{"firstname": "Joe", "sum_salary": 12}],
        )