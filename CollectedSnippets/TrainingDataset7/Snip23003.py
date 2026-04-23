def test_more_initial_than_max_num(self):
        """
        More initial forms than max_num results in all initial forms being
        displayed (but no extra forms).
        """
        initial = [
            {"name": "Gin Tonic"},
            {"name": "Bloody Mary"},
            {"name": "Jack and Coke"},
        ]
        LimitedFavoriteDrinkFormSet = formset_factory(
            FavoriteDrinkForm, extra=1, max_num=2
        )
        formset = LimitedFavoriteDrinkFormSet(initial=initial)
        self.assertHTMLEqual(
            "\n".join(str(form) for form in formset.forms),
            """
            <div><label for="id_form-0-name">Name:</label>
            <input id="id_form-0-name" name="form-0-name" type="text" value="Gin Tonic">
            </div>
            <div><label for="id_form-1-name">Name:</label>
            <input id="id_form-1-name" name="form-1-name" type="text"
                value="Bloody Mary"></div>
            <div><label for="id_form-2-name">Name:</label>
            <input id="id_form-2-name" name="form-2-name" type="text"
                value="Jack and Coke"></div>
            """,
        )