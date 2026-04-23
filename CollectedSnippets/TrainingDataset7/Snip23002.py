def test_max_num_zero_with_initial(self):
        # initial trumps max_num
        initial = [
            {"name": "Fernet and Coke"},
            {"name": "Bloody Mary"},
        ]
        LimitedFavoriteDrinkFormSet = formset_factory(
            FavoriteDrinkForm, extra=1, max_num=0
        )
        formset = LimitedFavoriteDrinkFormSet(initial=initial)
        self.assertHTMLEqual(
            "\n".join(str(form) for form in formset.forms),
            """
            <div><label for="id_form-0-name">Name:</label>
            <input id="id_form-0-name" name="form-0-name" type="text"
                value="Fernet and Coke"></div>
            <div><label for="id_form-1-name">Name:</label>
            <input id="id_form-1-name" name="form-1-name" type="text"
                value="Bloody Mary"></div>
            """,
        )