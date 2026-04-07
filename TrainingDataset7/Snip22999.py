def test_limiting_extra_lest_than_max_num(self):
        """max_num has no effect when extra is less than max_num."""
        LimitedFavoriteDrinkFormSet = formset_factory(
            FavoriteDrinkForm, extra=1, max_num=2
        )
        formset = LimitedFavoriteDrinkFormSet()
        self.assertHTMLEqual(
            "\n".join(str(form) for form in formset.forms),
            """<div><label for="id_form-0-name">Name:</label>
<input type="text" name="form-0-name" id="id_form-0-name"></div>""",
        )