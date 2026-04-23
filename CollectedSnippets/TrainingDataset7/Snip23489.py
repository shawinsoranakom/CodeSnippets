def test_initial_count(self):
        GenericFormSet = generic_inlineformset_factory(TaggedItem)
        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "3",
            "form-MAX_NUM_FORMS": "",
        }
        formset = GenericFormSet(data=data, prefix="form")
        self.assertEqual(formset.initial_form_count(), 3)
        formset = GenericFormSet(data=data, prefix="form", save_as_new=True)
        self.assertEqual(formset.initial_form_count(), 0)