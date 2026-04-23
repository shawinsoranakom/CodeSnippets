def test_initial_datetime_values(self):
        now = datetime.datetime.now()
        # Nix microseconds (since they should be ignored). #22502
        now_no_ms = now.replace(microsecond=0)
        if now == now_no_ms:
            now = now.replace(microsecond=1)

        def delayed_now():
            return now

        def delayed_now_time():
            return now.time()

        class HiddenInputWithoutMicrosec(HiddenInput):
            supports_microseconds = False

        class TextInputWithoutMicrosec(TextInput):
            supports_microseconds = False

        class DateTimeForm(Form):
            # Test a non-callable.
            fixed = DateTimeField(initial=now)
            auto_timestamp = DateTimeField(initial=delayed_now)
            auto_time_only = TimeField(initial=delayed_now_time)
            supports_microseconds = DateTimeField(initial=delayed_now, widget=TextInput)
            hi_default_microsec = DateTimeField(initial=delayed_now, widget=HiddenInput)
            hi_without_microsec = DateTimeField(
                initial=delayed_now, widget=HiddenInputWithoutMicrosec
            )
            ti_without_microsec = DateTimeField(
                initial=delayed_now, widget=TextInputWithoutMicrosec
            )

        unbound = DateTimeForm()
        cases = [
            ("fixed", now_no_ms),
            ("auto_timestamp", now_no_ms),
            ("auto_time_only", now_no_ms.time()),
            ("supports_microseconds", now),
            ("hi_default_microsec", now),
            ("hi_without_microsec", now_no_ms),
            ("ti_without_microsec", now_no_ms),
        ]
        for field_name, expected in cases:
            with self.subTest(field_name=field_name):
                actual = unbound[field_name].value()
                self.assertEqual(actual, expected)
                # Also check get_initial_for_field().
                field = unbound.fields[field_name]
                actual = unbound.get_initial_for_field(field, field_name)
                self.assertEqual(actual, expected)