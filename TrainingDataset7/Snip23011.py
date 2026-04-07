def test_non_form_errors(self):
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
        self.assertEqual(
            formset.non_form_errors(), ["You may only specify a drink once."]
        )
        self.assertEqual(
            str(formset.non_form_errors()),
            '<ul class="errorlist nonform"><li>'
            "You may only specify a drink once.</li></ul>",
        )