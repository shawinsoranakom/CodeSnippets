def test_single_form_completed(self):
        """Just one form may be completed."""
        data = {
            "choices-TOTAL_FORMS": "3",  # the number of forms rendered
            "choices-INITIAL_FORMS": "0",  # the number of forms with initial data
            "choices-MIN_NUM_FORMS": "0",  # min number of forms
            "choices-MAX_NUM_FORMS": "0",  # max number of forms
            "choices-0-choice": "Calexico",
            "choices-0-votes": "100",
            "choices-1-choice": "",
            "choices-1-votes": "",
            "choices-2-choice": "",
            "choices-2-votes": "",
        }
        ChoiceFormSet = formset_factory(Choice, extra=3)
        formset = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.assertTrue(formset.is_valid())
        self.assertEqual(
            [form.cleaned_data for form in formset.forms],
            [{"votes": 100, "choice": "Calexico"}, {}, {}],
        )