def test_invalid_start_value_range(self):
        msg = "start argument must be a negative integer, zero, or None, but got '3'."
        with self.assertRaisesMessage(ValueError, msg):
            list(
                Employee.objects.annotate(
                    test=Window(
                        expression=Sum("salary"),
                        order_by=F("hire_date").asc(),
                        frame=ValueRange(start=3),
                    )
                )
            )