def test_row_number_no_ordering(self):
        """
        The row number window function computes the number based on the order
        in which the tuples were inserted.
        """
        # Add a default ordering for consistent results across databases.
        qs = Employee.objects.annotate(
            row_number=Window(
                expression=RowNumber(),
            )
        ).order_by("pk")
        self.assertQuerySetEqual(
            qs,
            [
                ("Jones", "Accounting", 1),
                ("Williams", "Accounting", 2),
                ("Jenson", "Accounting", 3),
                ("Adams", "Accounting", 4),
                ("Smith", "Sales", 5),
                ("Brown", "Sales", 6),
                ("Johnson", "Marketing", 7),
                ("Smith", "Marketing", 8),
                ("Wilkinson", "IT", 9),
                ("Moore", "IT", 10),
                ("Miller", "Management", 11),
                ("Johnson", "Management", 12),
            ],
            lambda entry: (entry.name, entry.department, entry.row_number),
        )