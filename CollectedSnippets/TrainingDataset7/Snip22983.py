def test_formset_validate_min_excludes_empty_forms(self):
        data = {
            "choices-TOTAL_FORMS": "2",
            "choices-INITIAL_FORMS": "0",
        }
        ChoiceFormSet = formset_factory(
            Choice, extra=2, min_num=1, validate_min=True, can_delete=True
        )
        formset = ChoiceFormSet(data, prefix="choices")
        self.assertFalse(formset.has_changed())
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset.non_form_errors(), ["Please submit at least 1 form."])