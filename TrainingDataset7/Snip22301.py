def test_flatpage_admin_form_url_validation(self):
        "The flatpage admin form correctly validates urls"
        self.assertTrue(
            FlatpageForm(data=dict(url="/new_flatpage/", **self.form_data)).is_valid()
        )
        self.assertTrue(
            FlatpageForm(
                data=dict(url="/some.special~chars/", **self.form_data)
            ).is_valid()
        )
        self.assertTrue(
            FlatpageForm(
                data=dict(url="/some.very_special~chars-here/", **self.form_data)
            ).is_valid()
        )

        self.assertFalse(
            FlatpageForm(data=dict(url="/a space/", **self.form_data)).is_valid()
        )
        self.assertFalse(
            FlatpageForm(data=dict(url="/a % char/", **self.form_data)).is_valid()
        )
        self.assertFalse(
            FlatpageForm(data=dict(url="/a ! char/", **self.form_data)).is_valid()
        )
        self.assertFalse(
            FlatpageForm(data=dict(url="/a & char/", **self.form_data)).is_valid()
        )
        self.assertFalse(
            FlatpageForm(data=dict(url="/a ? char/", **self.form_data)).is_valid()
        )