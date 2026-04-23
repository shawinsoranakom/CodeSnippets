def test_max_num_zero(self):
        """
        If max_num is 0 then no form is rendered at all, regardless of extra,
        unless initial data is present.
        """
        LimitedFavoriteDrinkFormSet = formset_factory(
            FavoriteDrinkForm, extra=1, max_num=0
        )
        formset = LimitedFavoriteDrinkFormSet()
        self.assertEqual(formset.forms, [])