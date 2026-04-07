def test_modelformset_factory_absolute_max_with_max_num(self):
        AuthorFormSet = modelformset_factory(
            Author,
            fields="__all__",
            max_num=20,
            absolute_max=100,
        )
        data = {
            "form-TOTAL_FORMS": "101",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
        }
        formset = AuthorFormSet(data=data)
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(len(formset.forms), 100)
        self.assertEqual(
            formset.non_form_errors(),
            ["Please submit at most 20 forms."],
        )