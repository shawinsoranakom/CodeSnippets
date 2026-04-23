def test_invalid_type_start_value_range(self):
        msg = "start argument must be a negative integer, zero, or None, but got 'a'."
        with self.assertRaisesMessage(ValueError, msg):
            list(
                Employee.objects.annotate(
                    test=Window(
                        expression=Sum("salary"),
                        frame=ValueRange(start="a"),
                    )
                )
            )