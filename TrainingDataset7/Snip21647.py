def test_order_by_decimalfield(self):
        qs = Employee.objects.annotate(
            rank=Window(expression=Rank(), order_by="bonus")
        ).order_by("-bonus", "id")
        self.assertQuerySetEqual(
            qs,
            [
                ("Miller", 250.0, 12),
                ("Johnson", 200.0, 11),
                ("Wilkinson", 150.0, 10),
                ("Smith", 137.5, 9),
                ("Brown", 132.5, 8),
                ("Adams", 125.0, 7),
                ("Jones", 112.5, 5),
                ("Jenson", 112.5, 5),
                ("Johnson", 100.0, 4),
                ("Smith", 95.0, 3),
                ("Williams", 92.5, 2),
                ("Moore", 85.0, 1),
            ],
            transform=lambda row: (row.name, float(row.bonus), row.rank),
        )