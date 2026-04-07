def test_invalid_end_value_range(self):
        msg = "end argument must be a positive integer, zero, or None, but got '-3'."
        with self.assertRaisesMessage(ValueError, msg):
            list(
                Employee.objects.annotate(
                    test=Window(
                        expression=Sum("salary"),
                        order_by=F("hire_date").asc(),
                        frame=ValueRange(end=-3),
                    )
                )
            )