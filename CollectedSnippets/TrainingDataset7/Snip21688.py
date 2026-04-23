def test_row_range_both_following(self):
        """
        A query with ROWS BETWEEN 1 FOLLOWING AND 2 FOLLOWING.
        The resulting sum is the sum of the following two (if they exist) rows
        according to the ordering clause.
        """
        qs = Employee.objects.annotate(
            sum=Window(
                expression=Sum("salary"),
                order_by=[F("hire_date").asc(), F("name").desc()],
                frame=RowRange(start=1, end=2),
            )
        ).order_by("hire_date")
        self.assertIn("ROWS BETWEEN 1 FOLLOWING AND 2 FOLLOWING", str(qs.query))
        self.assertQuerySetEqual(
            qs,
            [
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), 125000),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), 100000),
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 100000),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), 82000),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 90000),
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), 91000),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), 98000),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), 100000),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), 90000),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), 84000),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), 34000),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), None),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.hire_date,
                row.sum,
            ),
        )