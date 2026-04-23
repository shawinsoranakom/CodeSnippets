def test_range_exclude_current(self):
        qs = Employee.objects.annotate(
            sum=Window(
                expression=Sum("salary"),
                order_by=F("salary").asc(),
                partition_by="department",
                frame=ValueRange(end=2, exclusion=WindowFrameExclusion.CURRENT_ROW),
            )
        ).order_by("department", "salary")
        self.assertIn(
            "RANGE BETWEEN UNBOUNDED PRECEDING AND 2 FOLLOWING EXCLUDE CURRENT ROW",
            str(qs.query),
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), None),
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 82000),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 82000),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), 127000),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), None),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), 34000),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), None),
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), 80000),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), None),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), 38000),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), None),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), 53000),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.hire_date,
                row.sum,
            ),
        )