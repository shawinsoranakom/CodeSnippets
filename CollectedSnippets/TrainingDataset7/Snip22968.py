def test_formset_validation_count(self):
        """
        A formset's ManagementForm is validated once per FormSet.is_valid()
        call and each form of the formset is cleaned once.
        """

        def make_method_counter(func):
            """Add a counter to func for the number of times it's called."""
            counter = Counter()
            counter.call_count = 0

            def mocked_func(*args, **kwargs):
                counter.call_count += 1
                return func(*args, **kwargs)

            return mocked_func, counter

        mocked_is_valid, is_valid_counter = make_method_counter(
            formsets.ManagementForm.is_valid
        )
        mocked_full_clean, full_clean_counter = make_method_counter(BaseForm.full_clean)
        formset = self.make_choiceformset(
            [("Calexico", "100"), ("Any1", "42"), ("Any2", "101")]
        )

        with (
            mock.patch(
                "django.forms.formsets.ManagementForm.is_valid", mocked_is_valid
            ),
            mock.patch("django.forms.forms.BaseForm.full_clean", mocked_full_clean),
        ):
            self.assertTrue(formset.is_valid())
        self.assertEqual(is_valid_counter.call_count, 1)
        self.assertEqual(full_clean_counter.call_count, 4)