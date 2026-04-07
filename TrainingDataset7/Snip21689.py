def test_distinct_window_function(self):
        """
        Window functions are not aggregates, and hence a query to filter out
        duplicates may be useful.
        """
        qs = (
            Employee.objects.annotate(
                sum=Window(
                    expression=Sum("salary"),
                    partition_by=ExtractYear("hire_date"),
                    order_by=ExtractYear("hire_date"),
                ),
                year=ExtractYear("hire_date"),
            )
            .filter(sum__gte=45000)
            .values("year", "sum")
            .distinct("year")
            .order_by("year")
        )
        results = [
            {"year": 2005, "sum": 225000},
            {"year": 2007, "sum": 55000},
            {"year": 2008, "sum": 45000},
            {"year": 2009, "sum": 128000},
            {"year": 2011, "sum": 60000},
            {"year": 2013, "sum": 84000},
        ]
        for idx, val in zip(range(len(results)), results):
            with self.subTest(result=val):
                self.assertEqual(qs[idx], val)