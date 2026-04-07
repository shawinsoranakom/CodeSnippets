def test_invalid_type_end_row_range(self):
        msg = "end argument must be an integer, zero, or None, but got 'a'."
        with self.assertRaisesMessage(ValueError, msg):
            list(
                Employee.objects.annotate(
                    test=Window(
                        expression=Sum("salary"),
                        frame=RowRange(end="a"),
                    )
                )
            )