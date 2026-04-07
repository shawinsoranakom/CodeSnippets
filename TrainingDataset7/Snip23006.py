def test_absolute_max_with_max_num(self):
        data = {
            "form-TOTAL_FORMS": "1001",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
        }
        LimitedFavoriteDrinksFormSet = formset_factory(
            FavoriteDrinkForm,
            max_num=30,
            absolute_max=1000,
        )
        formset = LimitedFavoriteDrinksFormSet(data=data)
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(len(formset.forms), 1000)
        self.assertEqual(
            formset.non_form_errors(),
            ["Please submit at most 30 forms."],
        )