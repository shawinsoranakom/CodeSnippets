def test_clean_hook(self):
        """
        FormSets have a clean() hook for doing extra validation that isn't tied
        to any form. It follows the same pattern as the clean() hook on Forms.
        """
        # Start out with a some duplicate data.
        data = {
            "drinks-TOTAL_FORMS": "2",  # the number of forms rendered
            "drinks-INITIAL_FORMS": "0",  # the number of forms with initial data
            "drinks-MIN_NUM_FORMS": "0",  # min number of forms
            "drinks-MAX_NUM_FORMS": "0",  # max number of forms
            "drinks-0-name": "Gin and Tonic",
            "drinks-1-name": "Gin and Tonic",
        }
        formset = FavoriteDrinksFormSet(data, prefix="drinks")
        self.assertFalse(formset.is_valid())
        # Any errors raised by formset.clean() are available via the
        # formset.non_form_errors() method.
        for error in formset.non_form_errors():
            self.assertEqual(str(error), "You may only specify a drink once.")
        # The valid case still works.
        data["drinks-1-name"] = "Bloody Mary"
        formset = FavoriteDrinksFormSet(data, prefix="drinks")
        self.assertTrue(formset.is_valid())
        self.assertEqual(formset.non_form_errors(), [])