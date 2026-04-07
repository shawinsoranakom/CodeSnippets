def test_datetime_clean_disabled_callable_initial_microseconds(self):
        """
        Cleaning a form with a disabled DateTimeField and callable initial
        removes microseconds.
        """
        form = self.get_datetime_form_with_callable_initial(
            disabled=True,
            microseconds=123456,
        )
        self.assertEqual(form.errors, {})
        self.assertEqual(
            form.cleaned_data,
            {
                "dt": datetime.datetime(2006, 10, 25, 14, 30, 46),
            },
        )