def test_limiting_max_forms(self):
        """Limiting the maximum number of forms with max_num."""
        # When not passed, max_num will take a high default value, leaving the
        # number of forms only controlled by the value of the extra parameter.
        LimitedFavoriteDrinkFormSet = formset_factory(FavoriteDrinkForm, extra=3)
        formset = LimitedFavoriteDrinkFormSet()
        self.assertHTMLEqual(
            "\n".join(str(form) for form in formset.forms),
            """<div><label for="id_form-0-name">Name:</label>
            <input type="text" name="form-0-name" id="id_form-0-name"></div>
<div><label for="id_form-1-name">Name:</label>
<input type="text" name="form-1-name" id="id_form-1-name"></div>
<div><label for="id_form-2-name">Name:</label>
<input type="text" name="form-2-name" id="id_form-2-name"></div>""",
        )
        # If max_num is 0 then no form is rendered at all.
        LimitedFavoriteDrinkFormSet = formset_factory(
            FavoriteDrinkForm, extra=3, max_num=0
        )
        formset = LimitedFavoriteDrinkFormSet()
        self.assertEqual(formset.forms, [])