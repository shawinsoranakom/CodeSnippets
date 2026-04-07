def test_row_range_both_preceding(self):
        """
        A query with ROWS BETWEEN 2 PRECEDING AND 1 PRECEDING.
        The resulting sum is the sum of the previous two (if they exist) rows
        according to the ordering clause.
        """
        qs = Employee.objects.annotate(
            sum=Window(
                expression=Sum("salary"),
                order_by=[F("hire_date").asc(), F("name").desc()],
                frame=RowRange(start=-2, end=-1),
            )
        ).order_by("hire_date")
        self.assertIn("ROWS BETWEEN 2 PRECEDING AND 1 PRECEDING", str(qs.query))
        self.assertQuerySetEqual(
            qs,
            [
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), None),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), 100000),
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 180000),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), 125000),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 100000),
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), 100000),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), 82000),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), 90000),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), 91000),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), 98000),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), 100000),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), 90000),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.hire_date,
                row.sum,
            ),
        )