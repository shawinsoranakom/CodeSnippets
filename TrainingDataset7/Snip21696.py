def test_invalid_start_end_value_for_row_range(self):
        msg = "start cannot be greater than end."
        with self.assertRaisesMessage(ValueError, msg):
            list(
                Employee.objects.annotate(
                    test=Window(
                        expression=Sum("salary"),
                        order_by=F("hire_date").asc(),
                        frame=RowRange(start=4, end=-3),
                    )
                )
            )