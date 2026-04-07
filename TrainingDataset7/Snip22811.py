def test_datetime_changed_data_callable_with_microseconds(self):
        class DateTimeForm(Form):
            dt = DateTimeField(
                initial=lambda: datetime.datetime(2006, 10, 25, 14, 30, 45, 123456),
                disabled=True,
            )

        form = DateTimeForm({"dt": "2006-10-25 14:30:45"})
        self.assertEqual(form.changed_data, [])