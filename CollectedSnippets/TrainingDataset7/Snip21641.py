def test_rank(self):
        """
        Rank the employees based on the year they're were hired. Since there
        are multiple employees hired in different years, this will contain
        gaps.
        """
        qs = Employee.objects.annotate(
            rank=Window(
                expression=Rank(),
                order_by=F("hire_date__year").asc(),
            )
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 1),
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), 1),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), 1),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), 4),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 5),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), 6),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), 6),
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), 6),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), 9),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), 10),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), 11),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), 11),
            ],
            lambda entry: (
                entry.name,
                entry.salary,
                entry.department,
                entry.hire_date,
                entry.rank,
            ),
            ordered=False,
        )