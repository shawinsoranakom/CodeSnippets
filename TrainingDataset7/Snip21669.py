def test_filter_values(self):
        qs = (
            Employee.objects.annotate(
                department_salary_rank=Window(
                    Rank(), partition_by="department", order_by="-salary"
                ),
            )
            .order_by("department", "name")
            .values_list(Upper("name"), flat=True)
        )
        self.assertSequenceEqual(
            qs.filter(department_salary_rank=1),
            ["ADAMS", "WILKINSON", "MILLER", "JOHNSON", "SMITH"],
        )