def test_empty_permitted(self):
        # Sometimes (pretty much in formsets) we want to allow a form to pass
        # validation if it is completely empty. We can accomplish this by using
        # the empty_permitted argument to a form constructor.
        class SongForm(Form):
            artist = CharField()
            name = CharField()

        # First let's show what happens id empty_permitted=False (the default):
        data = {"artist": "", "song": ""}
        form = SongForm(data, empty_permitted=False)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "name": ["This field is required."],
                "artist": ["This field is required."],
            },
        )
        self.assertEqual(form.cleaned_data, {})

        # Now let's show what happens when empty_permitted=True and the form is
        # empty.
        form = SongForm(data, empty_permitted=True, use_required_attribute=False)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})
        self.assertEqual(form.cleaned_data, {})

        # But if we fill in data for one of the fields, the form is no longer
        # empty and the whole thing must pass validation.
        data = {"artist": "The Doors", "song": ""}
        form = SongForm(data, empty_permitted=False)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"name": ["This field is required."]})
        self.assertEqual(form.cleaned_data, {"artist": "The Doors"})

        # If a field is not given in the data then None is returned for its
        # data. Lets make sure that when checking for empty_permitted that None
        # is treated accordingly.
        data = {"artist": None, "song": ""}
        form = SongForm(data, empty_permitted=True, use_required_attribute=False)
        self.assertTrue(form.is_valid())

        # However, we *really* need to be sure we are checking for None as any
        # data in initial that returns False on a boolean call needs to be
        # treated literally.
        class PriceForm(Form):
            amount = FloatField()
            qty = IntegerField()

        data = {"amount": "0.0", "qty": ""}
        form = PriceForm(
            data,
            initial={"amount": 0.0},
            empty_permitted=True,
            use_required_attribute=False,
        )
        self.assertTrue(form.is_valid())