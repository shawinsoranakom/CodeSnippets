def test_max_per_year(self):
        """
        Find the maximum salary awarded in the same year as the
        employee was hired, regardless of the department.
        """
        qs = Employee.objects.annotate(
            max_salary_year=Window(
                expression=Max("salary"),
                order_by=ExtractYear("hire_date").asc(),
                partition_by=ExtractYear("hire_date"),
            )
        ).order_by(ExtractYear("hire_date"), "salary")
        self.assertQuerySetEqual(
            qs,
            [
                ("Jones", "Accounting", 45000, 2005, 100000),
                ("Johnson", "Management", 80000, 2005, 100000),
                ("Miller", "Management", 100000, 2005, 100000),
                ("Smith", "Sales", 55000, 2007, 55000),
                ("Jenson", "Accounting", 45000, 2008, 45000),
                ("Williams", "Accounting", 37000, 2009, 53000),
                ("Smith", "Marketing", 38000, 2009, 53000),
                ("Brown", "Sales", 53000, 2009, 53000),
                ("Wilkinson", "IT", 60000, 2011, 60000),
                ("Johnson", "Marketing", 40000, 2012, 40000),
                ("Moore", "IT", 34000, 2013, 50000),
                ("Adams", "Accounting", 50000, 2013, 50000),
            ],
            lambda row: (
                row.name,
                row.department,
                row.salary,
                row.hire_date.year,
                row.max_salary_year,
            ),
        )