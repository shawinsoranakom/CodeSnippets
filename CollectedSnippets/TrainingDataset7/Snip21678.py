def test_range_unbound(self):
        """
        A query with RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING.
        """
        qs = Employee.objects.annotate(
            sum=Window(
                expression=Sum("salary"),
                partition_by="age",
                order_by=[F("age").asc()],
                frame=ValueRange(start=None, end=None),
            )
        ).order_by("department", "hire_date", "name")
        self.assertIn(
            "RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING", str(qs.query)
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("Jones", "Accounting", 45000, datetime.date(2005, 11, 1), 165000),
                ("Jenson", "Accounting", 45000, datetime.date(2008, 4, 1), 165000),
                ("Williams", "Accounting", 37000, datetime.date(2009, 6, 1), 165000),
                ("Adams", "Accounting", 50000, datetime.date(2013, 7, 1), 130000),
                ("Wilkinson", "IT", 60000, datetime.date(2011, 3, 1), 194000),
                ("Moore", "IT", 34000, datetime.date(2013, 8, 1), 194000),
                ("Miller", "Management", 100000, datetime.date(2005, 6, 1), 194000),
                ("Johnson", "Management", 80000, datetime.date(2005, 7, 1), 130000),
                ("Smith", "Marketing", 38000, datetime.date(2009, 10, 1), 165000),
                ("Johnson", "Marketing", 40000, datetime.date(2012, 3, 1), 148000),
                ("Smith", "Sales", 55000, datetime.date(2007, 6, 1), 148000),
                ("Brown", "Sales", 53000, datetime.date(2009, 9, 1), 148000),
            ],
            transform=lambda row: (
                row.name,
                row.department,
                row.salary,
                row.hire_date,
                row.sum,
            ),
        )