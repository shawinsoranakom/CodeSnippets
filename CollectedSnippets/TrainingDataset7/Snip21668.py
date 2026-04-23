def test_filter_column_ref_rhs(self):
        qs = (
            Employee.objects.annotate(
                max_dept_salary=Window(Max("salary"), partition_by="department")
            )
            .filter(max_dept_salary=F("salary"))
            .order_by("name")
            .values_list("name", flat=True)
        )
        self.assertSequenceEqual(
            qs, ["Adams", "Johnson", "Miller", "Smith", "Wilkinson"]
        )