def test_avg_salary_department(self):
        qs = Employee.objects.annotate(
            avg_salary=Window(
                expression=Avg("salary"),
                order_by=F("department").asc(),
                partition_by="department",
            )
        ).order_by("department", "-salary", "name")
        self.assertQuerySetEqual(
            qs,
            [
                ("Adams", 50000, "Accounting", 44250.00),
                ("Jenson", 45000, "Accounting", 44250.00),
                ("Jones", 45000, "Accounting", 44250.00),
                ("Williams", 37000, "Accounting", 44250.00),
                ("Wilkinson", 60000, "IT", 47000.00),
                ("Moore", 34000, "IT", 47000.00),
                ("Miller", 100000, "Management", 90000.00),
                ("Johnson", 80000, "Management", 90000.00),
                ("Johnson", 40000, "Marketing", 39000.00),
                ("Smith", 38000, "Marketing", 39000.00),
                ("Smith", 55000, "Sales", 54000.00),
                ("Brown", 53000, "Sales", 54000.00),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.avg_salary,
            ),
        )