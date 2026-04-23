def test_trunc_invalid_arguments(self):
        msg = "output_field must be either DateField, TimeField, or DateTimeField"
        with self.assertRaisesMessage(ValueError, msg):
            list(
                DTModel.objects.annotate(
                    truncated=Trunc(
                        "start_datetime", "year", output_field=IntegerField()
                    ),
                )
            )
        msg = "'name' isn't a DateField, TimeField, or DateTimeField."
        with self.assertRaisesMessage(TypeError, msg):
            list(
                DTModel.objects.annotate(
                    truncated=Trunc("name", "year", output_field=DateTimeField()),
                )
            )
        msg = "Cannot truncate DateField 'start_date' to DateTimeField"
        with self.assertRaisesMessage(ValueError, msg):
            list(DTModel.objects.annotate(truncated=Trunc("start_date", "second")))
        with self.assertRaisesMessage(ValueError, msg):
            list(
                DTModel.objects.annotate(
                    truncated=Trunc(
                        "start_date", "month", output_field=DateTimeField()
                    ),
                )
            )
        msg = "Cannot truncate TimeField 'start_time' to DateTimeField"
        with self.assertRaisesMessage(ValueError, msg):
            list(DTModel.objects.annotate(truncated=Trunc("start_time", "month")))
        with self.assertRaisesMessage(ValueError, msg):
            list(
                DTModel.objects.annotate(
                    truncated=Trunc(
                        "start_time", "second", output_field=DateTimeField()
                    ),
                )
            )