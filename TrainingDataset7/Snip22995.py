def test_invalid_deleted_form_with_ordering(self):
        """
        Can get ordered_forms from a valid formset even if a deleted form
        would have been invalid.
        """
        FavoriteDrinkFormset = formset_factory(
            form=FavoriteDrinkForm, can_delete=True, can_order=True
        )
        formset = FavoriteDrinkFormset(
            {
                "form-0-name": "",
                "form-0-DELETE": "on",  # no name!
                "form-TOTAL_FORMS": 1,
                "form-INITIAL_FORMS": 1,
                "form-MIN_NUM_FORMS": 0,
                "form-MAX_NUM_FORMS": 1,
            }
        )
        self.assertTrue(formset.is_valid())
        self.assertEqual(formset.ordered_forms, [])