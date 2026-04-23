def test_flatpage_admin_form_url_uniqueness_validation(self):
        """
        The flatpage admin form correctly enforces url uniqueness among
        flatpages of the same site.
        """
        data = dict(url="/myflatpage1/", **self.form_data)

        FlatpageForm(data=data).save()

        f = FlatpageForm(data=data)

        with translation.override("en"):
            self.assertFalse(f.is_valid())

            self.assertEqual(
                f.errors,
                {
                    "__all__": [
                        "Flatpage with url /myflatpage1/ already exists for site "
                        "example.com"
                    ]
                },
            )