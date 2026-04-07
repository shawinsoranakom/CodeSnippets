def test_default_absolute_max(self):
        # absolute_max defaults to 2 * DEFAULT_MAX_NUM if max_num is None.
        data = {
            "form-TOTAL_FORMS": 2001,
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
        }
        formset = FavoriteDrinksFormSet(data=data)
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(
            formset.non_form_errors(),
            ["Please submit at most 1000 forms."],
        )
        self.assertEqual(formset.absolute_max, 2000)