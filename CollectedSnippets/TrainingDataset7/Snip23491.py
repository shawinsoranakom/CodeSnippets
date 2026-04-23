def test_absolute_max(self):
        GenericFormSet = generic_inlineformset_factory(TaggedItem, absolute_max=1500)
        data = {
            "form-TOTAL_FORMS": "1501",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
        }
        formset = GenericFormSet(data=data, prefix="form")
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(len(formset.forms), 1500)
        self.assertEqual(
            formset.non_form_errors(),
            ["Please submit at most 1000 forms."],
        )