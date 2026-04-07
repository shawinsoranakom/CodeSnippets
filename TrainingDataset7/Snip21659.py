def test_percent_rank(self):
        """
        Calculate the percentage rank of the employees across the entire
        company based on salary and name (in case of ambiguity).
        """
        qs = Employee.objects.annotate(
            percent_rank=Window(
                expression=PercentRank(),
                order_by=[F("salary").asc(), F("name").asc()],
            )
        ).order_by("percent_rank")
        # Round to account for precision differences among databases.
        self.assertQuerySetEqual(
            qs,
            [
                ("Moore", "IT", 34000, 0.0),
                ("Williams", "Accounting", 37000, 0.0909090909),
                ("Smith", "Marketing", 38000, 0.1818181818),
                ("Johnson", "Marketing", 40000, 0.2727272727),
                ("Jenson", "Accounting", 45000, 0.3636363636),
                ("Jones", "Accounting", 45000, 0.4545454545),
                ("Adams", "Accounting", 50000, 0.5454545455),
                ("Brown", "Sales", 53000, 0.6363636364),
                ("Smith", "Sales", 55000, 0.7272727273),
                ("Wilkinson", "IT", 60000, 0.8181818182),
                ("Johnson", "Management", 80000, 0.9090909091),
                ("Miller", "Management", 100000, 1.0),
            ],
            transform=lambda row: (
                row.name,
                row.department,
                row.salary,
                round(row.percent_rank, 10),
            ),
        )