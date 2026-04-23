def test_row_range_rank_exclude_current_row(self):
        qs = Employee.objects.annotate(
            avg_salary_cohort=Window(
                expression=Avg("salary"),
                order_by=[F("hire_date").asc(), F("name").desc()],
                frame=RowRange(
                    start=-1, end=1, exclusion=WindowFrameExclusion.CURRENT_ROW
                ),
            )
        ).order_by("hire_date")
        self.assertIn(
            "ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING EXCLUDE CURRENT ROW",
            str(qs.query),
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), 80000),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), 72500),
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 67500),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), 45000),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 46000),
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), 49000),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), 37500),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), 56500),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), 39000),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), 55000),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), 37000),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), 50000),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.hire_date,
                row.avg_salary_cohort,
            ),
        )