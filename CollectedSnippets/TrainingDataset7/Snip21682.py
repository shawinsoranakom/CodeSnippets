def test_row_range_rank_exclude_ties(self):
        qs = Employee.objects.annotate(
            sum_salary_cohort=Window(
                expression=Sum("salary"),
                order_by=[F("hire_date").asc(), F("name").desc()],
                frame=RowRange(start=-1, end=1, exclusion=WindowFrameExclusion.TIES),
            )
        ).order_by("hire_date")
        self.assertIn(
            "ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING EXCLUDE TIES",
            str(qs.query),
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), 180000),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), 225000),
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 180000),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), 145000),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 137000),
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), 135000),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), 128000),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), 151000),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), 138000),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), 150000),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), 124000),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), 84000),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.hire_date,
                row.sum_salary_cohort,
            ),
        )