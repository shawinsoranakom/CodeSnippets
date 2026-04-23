def test_lead_offset(self):
        """
        Determine what the person hired after someone makes. Due to
        ambiguity, the name is also included in the ordering.
        """
        qs = Employee.objects.annotate(
            lead=Window(
                expression=Lead("salary", offset=2),
                partition_by="department",
                order_by=F("hire_date").asc(),
            )
        )
        self.assertQuerySetEqual(
            qs,
            [
                ("Jones", 45000, "Accounting", datetime.date(2005, 11, 1), 37000),
                ("Jenson", 45000, "Accounting", datetime.date(2008, 4, 1), 50000),
                ("Williams", 37000, "Accounting", datetime.date(2009, 6, 1), None),
                ("Adams", 50000, "Accounting", datetime.date(2013, 7, 1), None),
                ("Wilkinson", 60000, "IT", datetime.date(2011, 3, 1), None),
                ("Moore", 34000, "IT", datetime.date(2013, 8, 1), None),
                ("Johnson", 80000, "Management", datetime.date(2005, 7, 1), None),
                ("Miller", 100000, "Management", datetime.date(2005, 6, 1), None),
                ("Smith", 38000, "Marketing", datetime.date(2009, 10, 1), None),
                ("Johnson", 40000, "Marketing", datetime.date(2012, 3, 1), None),
                ("Smith", 55000, "Sales", datetime.date(2007, 6, 1), None),
                ("Brown", 53000, "Sales", datetime.date(2009, 9, 1), None),
            ],
            transform=lambda row: (
                row.name,
                row.salary,
                row.department,
                row.hire_date,
                row.lead,
            ),
            ordered=False,
        )