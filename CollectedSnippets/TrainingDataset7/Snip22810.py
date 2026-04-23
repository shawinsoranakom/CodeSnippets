def test_datetime_clean_disabled_callable_initial_bound_field(self):
        """
        The cleaned value for a form with a disabled DateTimeField and callable
        initial matches the bound field's cached initial value.
        """
        form = self.get_datetime_form_with_callable_initial(disabled=True)
        self.assertEqual(form.errors, {})
        cleaned = form.cleaned_data["dt"]
        self.assertEqual(cleaned, datetime.datetime(2006, 10, 25, 14, 30, 46))
        bf = form["dt"]
        self.assertEqual(cleaned, bf.initial)