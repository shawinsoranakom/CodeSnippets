def test_lag(self):
        """
        Compute the difference between an employee's salary and the next
        highest salary in the employee's department. Return None if the
        employee has the lowest salary.
        """
        qs = Employee.objects.annotate(
            lag=Window(
                expression=Lag(expression="salary", offset=1),
                partition_by=F("department"),
                order_by=[F("salary").asc(), F("name").asc()],
            )
        ).order_by("department", F("salary").asc(), F("name").asc())
        self.assertQuerySetEqual(
            qs,
            [
                ("Williams", 37000, "Accounting", None),
                ("Jenson", 45000, "Accounting", 37000),
                ("Jones", 45000, "Accounting", 45000),
                ("Adams", 50000, "Accounting", 45000),
                ("Moore", 34000, "IT", None),
                ("Wilkinson", 60000, "IT", 34000),
                ("Johnson", 80000, "Management", None),
                ("Miller", 100000, "Management", 80000),
                ("Smith", 38000, "Marketing", None),
                ("Johnson", 40000, "Marketing", 38000),
                ("Brown", 53000, "Sales", None),
                ("Smith", 55000, "Sales", 53000),
            ],
            transform=lambda row: (row.name, row.salary, row.department, row.lag),
        )