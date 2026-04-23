def test_modelformset_min_num_equals_max_num_less_than(self):
        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "2",
            "form-0-slug": "car-red",
            "form-1-slug": "car-blue",
            "form-2-slug": "car-black",
        }
        FormSet = modelformset_factory(
            Product,
            fields="__all__",
            extra=1,
            max_num=2,
            validate_max=True,
            min_num=2,
            validate_min=True,
        )
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset.non_form_errors(), ["Please submit at most 2 forms."])