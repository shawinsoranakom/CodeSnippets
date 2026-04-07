def test_min_department(self):
        """An alternative way to specify a query for FirstValue."""
        qs = Employee.objects.annotate(
            min_salary=Window(
                expression=Min("salary"),
                partition_by=F("department"),
                order_by=[F("salary").asc(), F("name").asc()],
            )
        ).order_by("department", "salary", "name")
        self.assertQuerySetEqual(
            qs,
            [
                ("Williams", "Accounting", 37000, 37000),
                ("Jenson", "Accounting", 45000, 37000),
                ("Jones", "Accounting", 45000, 37000),
                ("Adams", "Accounting", 50000, 37000),
                ("Moore", "IT", 34000, 34000),
                ("Wilkinson", "IT", 60000, 34000),
                ("Johnson", "Management", 80000, 80000),
                ("Miller", "Management", 100000, 80000),
                ("Smith", "Marketing", 38000, 38000),
                ("Johnson", "Marketing", 40000, 38000),
                ("Brown", "Sales", 53000, 53000),
                ("Smith", "Sales", 55000, 53000),
            ],
            lambda row: (row.name, row.department, row.salary, row.min_salary),
        )