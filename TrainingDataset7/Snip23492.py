def test_absolute_max_with_max_num(self):
        GenericFormSet = generic_inlineformset_factory(
            TaggedItem,
            max_num=20,
            absolute_max=100,
        )
        data = {
            "form-TOTAL_FORMS": "101",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
        }
        formset = GenericFormSet(data=data, prefix="form")
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(len(formset.forms), 100)
        self.assertEqual(
            formset.non_form_errors(),
            ["Please submit at most 20 forms."],
        )