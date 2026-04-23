def test_hard_limit_on_instantiated_forms(self):
        """A formset has a hard limit on the number of forms instantiated."""
        # reduce the default limit of 1000 temporarily for testing
        _old_DEFAULT_MAX_NUM = formsets.DEFAULT_MAX_NUM
        try:
            formsets.DEFAULT_MAX_NUM = 2
            ChoiceFormSet = formset_factory(Choice, max_num=1)
            # someone fiddles with the mgmt form data...
            formset = ChoiceFormSet(
                {
                    "choices-TOTAL_FORMS": "4",
                    "choices-INITIAL_FORMS": "0",
                    "choices-MIN_NUM_FORMS": "0",  # min number of forms
                    "choices-MAX_NUM_FORMS": "4",
                    "choices-0-choice": "Zero",
                    "choices-0-votes": "0",
                    "choices-1-choice": "One",
                    "choices-1-votes": "1",
                    "choices-2-choice": "Two",
                    "choices-2-votes": "2",
                    "choices-3-choice": "Three",
                    "choices-3-votes": "3",
                },
                prefix="choices",
            )
            # But we still only instantiate 3 forms
            self.assertEqual(len(formset.forms), 3)
            # and the formset isn't valid
            self.assertFalse(formset.is_valid())
        finally:
            formsets.DEFAULT_MAX_NUM = _old_DEFAULT_MAX_NUM