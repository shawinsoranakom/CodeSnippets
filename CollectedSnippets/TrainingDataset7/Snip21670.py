def test_filter_alias(self):
        qs = Employee.objects.alias(
            department_avg_age_diff=(
                Window(Avg("age"), partition_by="department") - F("age")
            ),
        ).order_by("department", "name")
        self.assertQuerySetEqual(
            qs.filter(department_avg_age_diff__gt=0),
            ["Jenson", "Jones", "Williams", "Miller", "Smith"],
            lambda employee: employee.name,
        )