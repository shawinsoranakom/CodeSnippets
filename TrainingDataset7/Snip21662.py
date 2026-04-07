def test_multiple_ordering(self):
        """
        Accumulate the salaries over the departments based on hire_date.
        If two people were hired on the same date in the same department, the
        ordering clause will render a different result for those people.
        """
        qs = Employee.objects.annotate(
            sum=Window(
                expression=Sum("salary"),
                partition_by="department",
                order_by=[F("hire_date").asc(), F("name").asc()],
            )
        ).order_by("department", "sum")
        self.assertQuerySetEqual(
            qs,
            [
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 45000),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 90000),
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), 127000),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), 177000),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), 60000),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), 94000),
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), 100000),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), 180000),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), 38000),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), 78000),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), 55000),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), 108000),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.hire_date,
                row.sum,
            ),
        )