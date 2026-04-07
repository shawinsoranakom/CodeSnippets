def test_ntile(self):
        """
        Compute the group for each of the employees across the entire company,
        based on how high the salary is for them. There are twelve employees
        so it divides evenly into four groups.
        """
        qs = Employee.objects.annotate(
            ntile=Window(
                expression=Ntile(num_buckets=4),
                order_by="-salary",
            )
        ).order_by("ntile", "-salary", "name")
        self.assertQuerySetEqual(
            qs,
            [
                ("Miller", "Management", 100000, 1),
                ("Johnson", "Management", 80000, 1),
                ("Wilkinson", "IT", 60000, 1),
                ("Smith", "Sales", 55000, 2),
                ("Brown", "Sales", 53000, 2),
                ("Adams", "Accounting", 50000, 2),
                ("Jenson", "Accounting", 45000, 3),
                ("Jones", "Accounting", 45000, 3),
                ("Johnson", "Marketing", 40000, 3),
                ("Smith", "Marketing", 38000, 4),
                ("Williams", "Accounting", 37000, 4),
                ("Moore", "IT", 34000, 4),
            ],
            lambda x: (x.name, x.department, x.salary, x.ntile),
        )