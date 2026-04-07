def test_empty_ordering(self):
        """
        Explicit empty ordering makes little sense but it is something that
        was historically allowed.
        """
        qs = Employee.objects.annotate(
            sum=Window(
                expression=Sum("salary"),
                partition_by="department",
                order_by=[],
            )
        ).order_by("department", "sum")
        self.assertEqual(len(qs), 12)