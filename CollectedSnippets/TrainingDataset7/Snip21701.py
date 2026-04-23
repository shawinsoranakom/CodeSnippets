def test_unsupported_range_frame_end(self):
        msg = (
            "%s only supports UNBOUNDED together with PRECEDING and FOLLOWING."
            % connection.display_name
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            list(
                Employee.objects.annotate(
                    test=Window(
                        expression=Sum("salary"),
                        order_by=F("hire_date").asc(),
                        frame=ValueRange(end=1),
                    )
                )
            )