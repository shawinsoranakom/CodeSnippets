def test_more_initial_form_result_in_one(self):
        """
        One form from initial and extra=3 with max_num=2 results in the one
        initial form and one extra.
        """
        LimitedFavoriteDrinkFormSet = formset_factory(
            FavoriteDrinkForm, extra=3, max_num=2
        )
        formset = LimitedFavoriteDrinkFormSet(initial=[{"name": "Gin Tonic"}])
        self.assertHTMLEqual(
            "\n".join(str(form) for form in formset.forms),
            """
            <div><label for="id_form-0-name">Name:</label>
            <input type="text" name="form-0-name" value="Gin Tonic" id="id_form-0-name">
            </div>
            <div><label for="id_form-1-name">Name:</label>
            <input type="text" name="form-1-name" id="id_form-1-name"></div>""",
        )