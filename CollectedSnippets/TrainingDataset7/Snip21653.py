def test_cume_dist(self):
        """
        Compute the cumulative distribution for the employees based on the
        salary in increasing order. Equal to rank/total number of rows (12).
        """
        qs = Employee.objects.annotate(
            cume_dist=Window(
                expression=CumeDist(),
                order_by=F("salary").asc(),
            )
        ).order_by("salary", "name")
        # Round result of cume_dist because Oracle uses greater precision.
        self.assertQuerySetEqual(
            qs,
            [
                ("Moore", "IT", 34000, 0.0833333333),
                ("Williams", "Accounting", 37000, 0.1666666667),
                ("Smith", "Marketing", 38000, 0.25),
                ("Johnson", "Marketing", 40000, 0.3333333333),
                ("Jenson", "Accounting", 45000, 0.5),
                ("Jones", "Accounting", 45000, 0.5),
                ("Adams", "Accounting", 50000, 0.5833333333),
                ("Brown", "Sales", 53000, 0.6666666667),
                ("Smith", "Sales", 55000, 0.75),
                ("Wilkinson", "IT", 60000, 0.8333333333),
                ("Johnson", "Management", 80000, 0.9166666667),
                ("Miller", "Management", 100000, 1),
            ],
            lambda row: (
                row.name,
                row.department,
                row.salary,
                round(row.cume_dist, 10),
            ),
        )