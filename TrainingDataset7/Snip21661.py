def test_multiple_partitioning(self):
        """
        Find the maximum salary for each department for people hired in the
        same year.
        """
        qs = Employee.objects.annotate(
            max=Window(
                expression=Max("salary"),
                partition_by=[F("department"), F("hire_date__year")],
            ),
            past_department_count=Count("past_departments"),
        ).order_by("department", "hire_date", "name")
        self.assertQuerySetEqual(
            qs,
            [
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 45000, 0),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 45000, 0),
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), 37000, 0),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), 50000, 0),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), 60000, 0),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), 34000, 0),
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), 100000, 1),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), 100000, 0),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), 38000, 0),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), 40000, 1),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), 55000, 0),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), 53000, 0),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.hire_date,
                row.max,
                row.past_department_count,
            ),
        )