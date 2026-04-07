def test_window_expression_within_subquery(self):
        subquery_qs = Employee.objects.annotate(
            highest=Window(
                FirstValue("id"),
                partition_by=F("department"),
                order_by=F("salary").desc(),
            )
        ).values("highest")
        highest_salary = Employee.objects.filter(pk__in=subquery_qs)
        self.assertCountEqual(
            highest_salary.values("department", "salary"),
            [
                {"department": "Accounting", "salary": 50000},
                {"department": "Sales", "salary": 55000},
                {"department": "Marketing", "salary": 40000},
                {"department": "IT", "salary": 60000},
                {"department": "Management", "salary": 100000},
            ],
        )