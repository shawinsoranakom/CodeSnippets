def test_modelformset_factory_absolute_max(self):
        AuthorFormSet = modelformset_factory(
            Author, fields="__all__", absolute_max=1500
        )
        data = {
            "form-TOTAL_FORMS": "1501",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
        }
        formset = AuthorFormSet(data=data)
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(len(formset.forms), 1500)
        self.assertEqual(
            formset.non_form_errors(),
            ["Please submit at most 1000 forms."],
        )