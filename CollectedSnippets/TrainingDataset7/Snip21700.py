def test_unsupported_range_frame_start(self):
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
                        frame=ValueRange(start=-1),
                    )
                )
            )