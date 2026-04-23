def test_window_repr(self):
        self.assertEqual(
            repr(Window(expression=Sum("salary"), partition_by="department")),
            "<Window: Sum(F(salary)) OVER (PARTITION BY F(department))>",
        )
        self.assertEqual(
            repr(Window(expression=Avg("salary"), order_by=F("department").asc())),
            "<Window: Avg(F(salary)) OVER (OrderBy(F(department), descending=False))>",
        )