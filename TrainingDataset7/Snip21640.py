def test_department_salary(self):
        qs = Employee.objects.annotate(
            department_sum=Window(
                expression=Sum("salary"),
                partition_by=F("department"),
                order_by=[F("hire_date").asc()],
            )
        ).order_by("department", "department_sum")
        self.assertQuerySetEqual(
            qs,
            [
                ("Jones", "Accounting", 45000, 45000),
                ("Jenson", "Accounting", 45000, 90000),
                ("Williams", "Accounting", 37000, 127000),
                ("Adams", "Accounting", 50000, 177000),
                ("Wilkinson", "IT", 60000, 60000),
                ("Moore", "IT", 34000, 94000),
                ("Miller", "Management", 100000, 100000),
                ("Johnson", "Management", 80000, 180000),
                ("Smith", "Marketing", 38000, 38000),
                ("Johnson", "Marketing", 40000, 78000),
                ("Smith", "Sales", 55000, 55000),
                ("Brown", "Sales", 53000, 108000),
            ],
            lambda entry: (
                entry.name,
                entry.department,
                entry.salary,
                entry.department_sum,
            ),
        )