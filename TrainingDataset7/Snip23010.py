def test_management_form_prefix(self):
        """The management form has the correct prefix."""
        formset = FavoriteDrinksFormSet()
        self.assertEqual(formset.management_form.prefix, "form")
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
        }
        formset = FavoriteDrinksFormSet(data=data)
        self.assertEqual(formset.management_form.prefix, "form")
        formset = FavoriteDrinksFormSet(initial={})
        self.assertEqual(formset.management_form.prefix, "form")