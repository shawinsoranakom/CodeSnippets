def test_nthvalue(self):
        qs = Employee.objects.annotate(
            nth_value=Window(
                expression=NthValue(expression="salary", nth=2),
                order_by=[F("hire_date").asc(), F("name").desc()],
                partition_by=F("department"),
            )
        ).order_by("department", "hire_date", "name")
        self.assertQuerySetEqual(
            qs,
            [
                ("Jones", "Accounting", datetime.date(2005, 11, 1), 45000, None),
                ("Jenson", "Accounting", datetime.date(2008, 4, 1), 45000, 45000),
                ("Williams", "Accounting", datetime.date(2009, 6, 1), 37000, 45000),
                ("Adams", "Accounting", datetime.date(2013, 7, 1), 50000, 45000),
                ("Wilkinson", "IT", datetime.date(2011, 3, 1), 60000, None),
                ("Moore", "IT", datetime.date(2013, 8, 1), 34000, 34000),
                ("Miller", "Management", datetime.date(2005, 6, 1), 100000, None),
                ("Johnson", "Management", datetime.date(2005, 7, 1), 80000, 80000),
                ("Smith", "Marketing", datetime.date(2009, 10, 1), 38000, None),
                ("Johnson", "Marketing", datetime.date(2012, 3, 1), 40000, 40000),
                ("Smith", "Sales", datetime.date(2007, 6, 1), 55000, None),
                ("Brown", "Sales", datetime.date(2009, 9, 1), 53000, 53000),
            ],
            lambda row: (
                row.name,
                row.department,
                row.hire_date,
                row.salary,
                row.nth_value,
            ),
        )