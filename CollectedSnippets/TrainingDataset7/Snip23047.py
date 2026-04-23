def test_valid(self):
        data = {
            "choices-TOTAL_FORMS": "2",
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
            "choices-0-choice": "Zero",
            "choices-0-votes": "0",
            "choices-1-choice": "One",
            "choices-1-votes": "1",
        }
        ChoiceFormSet = formset_factory(Choice)
        formset1 = ChoiceFormSet(data, auto_id=False, prefix="choices")
        formset2 = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.assertIs(all_valid((formset1, formset2)), True)
        expected_errors = [{}, {}]
        self.assertEqual(formset1._errors, expected_errors)
        self.assertEqual(formset2._errors, expected_errors)