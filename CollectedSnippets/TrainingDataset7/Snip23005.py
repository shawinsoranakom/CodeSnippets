def test_absolute_max(self):
        data = {
            "form-TOTAL_FORMS": "2001",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
        }
        AbsoluteMaxFavoriteDrinksFormSet = formset_factory(
            FavoriteDrinkForm,
            absolute_max=3000,
        )
        formset = AbsoluteMaxFavoriteDrinksFormSet(data=data)
        self.assertIs(formset.is_valid(), True)
        self.assertEqual(len(formset.forms), 2001)
        # absolute_max provides a hard limit.
        data["form-TOTAL_FORMS"] = "3001"
        formset = AbsoluteMaxFavoriteDrinksFormSet(data=data)
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(len(formset.forms), 3000)
        self.assertEqual(
            formset.non_form_errors(),
            ["Please submit at most 1000 forms."],
        )