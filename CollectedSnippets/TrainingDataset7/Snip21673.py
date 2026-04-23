def test_heterogeneous_filter(self):
        qs = (
            Employee.objects.annotate(
                department_salary_rank=Window(
                    Rank(), partition_by="department", order_by="-salary"
                ),
            )
            .order_by("name")
            .values_list("name", flat=True)
        )
        # Heterogeneous filter between window function and aggregates pushes
        # the WHERE clause to the QUALIFY outer query.
        self.assertSequenceEqual(
            qs.filter(
                department_salary_rank=1, department__in=["Accounting", "Management"]
            ),
            ["Adams", "Miller"],
        )
        self.assertSequenceEqual(
            qs.filter(
                Q(department_salary_rank=1)
                | Q(department__in=["Accounting", "Management"])
            ),
            [
                "Adams",
                "Jenson",
                "Johnson",
                "Johnson",
                "Jones",
                "Miller",
                "Smith",
                "Wilkinson",
                "Williams",
            ],
        )
        # Heterogeneous filter between window function and aggregates pushes
        # the HAVING clause to the QUALIFY outer query.
        qs = qs.annotate(past_department_count=Count("past_departments"))
        self.assertSequenceEqual(
            qs.filter(department_salary_rank=1, past_department_count__gte=1),
            ["Johnson", "Miller"],
        )
        self.assertSequenceEqual(
            qs.filter(Q(department_salary_rank=1) | Q(past_department_count__gte=1)),
            ["Adams", "Johnson", "Miller", "Smith", "Wilkinson"],
        )