def test_limited_filter(self):
        """
        A query filtering against a window function have its limit applied
        after window filtering takes place.
        """
        self.assertQuerySetEqual(
            Employee.objects.annotate(
                department_salary_rank=Window(
                    Rank(), partition_by="department", order_by="-salary"
                )
            )
            .filter(department_salary_rank=1)
            .order_by("department")[0:3],
            ["Adams", "Wilkinson", "Miller"],
            lambda employee: employee.name,
        )