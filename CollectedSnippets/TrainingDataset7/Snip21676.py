def test_range_n_preceding_and_following(self):
        qs = Employee.objects.annotate(
            sum=Window(
                expression=Sum("salary"),
                order_by=F("salary").asc(),
                partition_by="department",
                frame=ValueRange(start=-2, end=2),
            )
        )
        self.assertIn("RANGE BETWEEN 2 PRECEDING AND 2 FOLLOWING", str(qs.query))
        self.assertQuerySetEqual(
            qs,
            [
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), 37000),
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 90000),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 90000),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), 50000),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), 53000),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), 55000),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), 40000),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), 38000),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), 60000),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), 34000),
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), 100000),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), 80000),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.hire_date,
                row.sum,
            ),
            ordered=False,
        )