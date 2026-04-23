def test_filter_select_related(self):
        qs = (
            Employee.objects.alias(
                department_avg_age_diff=(
                    Window(Avg("age"), partition_by="department") - F("age")
                ),
            )
            .select_related("classification")
            .filter(department_avg_age_diff__gt=0)
            .order_by("department", "name")
        )
        self.assertQuerySetEqual(
            qs,
            ["Jenson", "Jones", "Williams", "Miller", "Smith"],
            lambda employee: employee.name,
        )
        with self.assertNumQueries(0):
            qs[0].classification