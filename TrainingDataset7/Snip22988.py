def test_formset_with_deletion_invalid_deleted_form(self):
        """
        deleted_forms works on a valid formset even if a deleted form would
        have been invalid.
        """
        FavoriteDrinkFormset = formset_factory(form=FavoriteDrinkForm, can_delete=True)
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
        self.assertEqual(formset._errors, [])
        self.assertEqual(len(formset.deleted_forms), 1)