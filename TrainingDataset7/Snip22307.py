def test_flatpage_nosites(self):
        data = dict(url="/myflatpage1/", **self.form_data)
        data.update({"sites": ""})

        f = FlatpageForm(data=data)

        self.assertFalse(f.is_valid())

        self.assertEqual(
            f.errors, {"sites": [translation.gettext("This field is required.")]}
        )