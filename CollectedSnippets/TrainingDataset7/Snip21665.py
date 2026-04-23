def test_filter(self):
        qs = Employee.objects.annotate(
            department_salary_rank=Window(
                Rank(), partition_by="department", order_by="-salary"
            ),
            department_avg_age_diff=(
                Window(Avg("age"), partition_by="department") - F("age")
            ),
        ).order_by("department", "name")
        # Direct window reference.
        self.assertQuerySetEqual(
            qs.filter(department_salary_rank=1),
            ["Adams", "Wilkinson", "Miller", "Johnson", "Smith"],
            lambda employee: employee.name,
        )
        # Through a combined expression containing a window.
        self.assertQuerySetEqual(
            qs.filter(department_avg_age_diff__gt=0),
            ["Jenson", "Jones", "Williams", "Miller", "Smith"],
            lambda employee: employee.name,
        )
        # Intersection of multiple windows.
        self.assertQuerySetEqual(
            qs.filter(department_salary_rank=1, department_avg_age_diff__gt=0),
            ["Miller"],
            lambda employee: employee.name,
        )
        # Union of multiple windows.
        self.assertQuerySetEqual(
            qs.filter(Q(department_salary_rank=1) | Q(department_avg_age_diff__gt=0)),
            [
                "Adams",
                "Jenson",
                "Jones",
                "Williams",
                "Wilkinson",
                "Miller",
                "Johnson",
                "Smith",
                "Smith",
            ],
            lambda employee: employee.name,
        )