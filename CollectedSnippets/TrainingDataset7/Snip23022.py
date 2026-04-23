def test_formset_total_error_count_with_non_form_errors(self):
        data = {
            "choices-TOTAL_FORMS": "2",  # the number of forms rendered
            "choices-INITIAL_FORMS": "0",  # the number of forms with initial data
            "choices-MAX_NUM_FORMS": "2",  # max number of forms - should be ignored
            "choices-0-choice": "Zero",
            "choices-0-votes": "0",
            "choices-1-choice": "One",
            "choices-1-votes": "1",
        }
        ChoiceFormSet = formset_factory(Choice, extra=1, max_num=1, validate_max=True)
        formset = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.assertEqual(formset.total_error_count(), 1)
        data["choices-1-votes"] = ""
        formset = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.assertEqual(formset.total_error_count(), 2)