def get_datetime_form_with_callable_initial(self, disabled, microseconds=0):
        class FakeTime:
            def __init__(self):
                self.elapsed_seconds = 0

            def now(self):
                self.elapsed_seconds += 1
                return datetime.datetime(
                    2006,
                    10,
                    25,
                    14,
                    30,
                    45 + self.elapsed_seconds,
                    microseconds,
                )

        class DateTimeForm(Form):
            dt = DateTimeField(initial=FakeTime().now, disabled=disabled)

        return DateTimeForm({})