def test_invalid_frame_exclusion_value_raises_error(self):
        msg = "RowRange.exclusion must be a WindowFrameExclusion instance."
        with self.assertRaisesMessage(TypeError, msg):
            Employee.objects.annotate(
                avg_salary_cohort=Window(
                    expression=Avg("salary"),
                    order_by=[F("hire_date").asc(), F("name").desc()],
                    frame=RowRange(start=-1, end=1, exclusion="RUBBISH"),
                )
            )