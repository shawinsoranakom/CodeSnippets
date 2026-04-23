def test_unsupported_frame_exclusion_raises_error(self):
        msg = "This backend does not support window frame exclusions."
        with self.assertRaisesMessage(NotSupportedError, msg):
            list(
                Employee.objects.annotate(
                    avg_salary_cohort=Window(
                        expression=Avg("salary"),
                        order_by=[F("hire_date").asc(), F("name").desc()],
                        frame=RowRange(
                            start=-1, end=1, exclusion=WindowFrameExclusion.CURRENT_ROW
                        ),
                    )
                )
            )